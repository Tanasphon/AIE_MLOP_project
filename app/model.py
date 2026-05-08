import json
from functools import lru_cache
from typing import Any

import numpy as np
import onnxruntime as ort
from PIL import Image
from transformers import AutoConfig, AutoImageProcessor

from app.config import settings
from app.image_utils import load_rgb_image


_onnx_session: ort.InferenceSession | None = None
_torch_model: Any | None = None


@lru_cache(maxsize=1)
def get_processor() -> AutoImageProcessor:
    return AutoImageProcessor.from_pretrained(settings.model_id)


@lru_cache(maxsize=1)
def get_labels() -> dict[int, str]:
    config_path = settings.onnx_model_path.parent / "config.json"
    if config_path.exists():
        with config_path.open("r", encoding="utf-8") as file:
            config = json.load(file)
        return {int(key): value for key, value in config["id2label"].items()}

    config = AutoConfig.from_pretrained(settings.model_id)
    return {int(key): value for key, value in config.id2label.items()}


@lru_cache(maxsize=1)
def get_preprocessor_config() -> dict[str, Any]:
    config_path = settings.onnx_model_path.parent / "preprocessor_config.json"
    if config_path.exists():
        with config_path.open("r", encoding="utf-8") as file:
            return json.load(file)

    return {
        "crop_size": {"height": 256, "width": 256},
        "do_center_crop": True,
        "do_flip_channel_order": True,
        "do_rescale": True,
        "rescale_factor": 1 / 255,
        "size": {"shortest_edge": 288},
    }


def preprocess_for_onnx(image_bytes: bytes) -> np.ndarray:
    image = load_rgb_image(image_bytes)
    config = get_preprocessor_config()
    shortest_edge = int(config["size"]["shortest_edge"])
    crop_height = int(config["crop_size"]["height"])
    crop_width = int(config["crop_size"]["width"])

    width, height = image.size
    if width <= height:
        resized_width = shortest_edge
        resized_height = round(height * shortest_edge / width)
    else:
        resized_height = shortest_edge
        resized_width = round(width * shortest_edge / height)

    image = image.resize((resized_width, resized_height), resample=Image.Resampling.BILINEAR)

    left = max((resized_width - crop_width) // 2, 0)
    top = max((resized_height - crop_height) // 2, 0)
    image = image.crop((left, top, left + crop_width, top + crop_height))

    array = np.asarray(image, dtype=np.float32)
    if config.get("do_flip_channel_order", False) or config.get("do_flip_channels", False):
        array = array[..., ::-1]
    if config.get("do_rescale", True):
        array *= float(config.get("rescale_factor", 1 / 255))

    return np.transpose(array, (2, 0, 1))[None, ...].astype(np.float32)


def _softmax(logits: np.ndarray) -> np.ndarray:
    shifted = logits - np.max(logits, axis=-1, keepdims=True)
    exp = np.exp(shifted)
    return exp / np.sum(exp, axis=-1, keepdims=True)


def _format_predictions(logits: np.ndarray, top_k: int) -> list[dict[str, Any]]:
    scores = _softmax(logits)[0]
    labels = get_labels()
    top_indexes = np.argsort(scores)[::-1][:top_k]
    return [
        {"label": labels.get(int(index), str(index)), "score": float(scores[index])}
        for index in top_indexes
    ]


def _get_onnx_session() -> tuple[ort.InferenceSession, str]:
    global _onnx_session

    model_path = settings.quantized_model_path
    runtime = "onnx-quantized"
    if not model_path.exists():
        model_path = settings.onnx_model_path
        runtime = "onnx"

    if _onnx_session is None:
        _onnx_session = ort.InferenceSession(
            str(model_path),
            providers=["CPUExecutionProvider"],
        )

    return _onnx_session, runtime


def _predict_onnx(image_bytes: bytes, top_k: int) -> tuple[str, list[dict[str, Any]]]:
    session, runtime = _get_onnx_session()
    input_name = session.get_inputs()[0].name
    logits = session.run(None, {input_name: preprocess_for_onnx(image_bytes)})[0]
    return runtime, _format_predictions(logits, top_k)


def _get_torch_model() -> Any:
    global _torch_model

    from transformers import AutoModelForImageClassification

    if _torch_model is None:
        _torch_model = AutoModelForImageClassification.from_pretrained(settings.model_id)
        _torch_model.eval()

    return _torch_model


def _predict_torch(image_bytes: bytes, top_k: int) -> tuple[str, list[dict[str, Any]]]:
    import torch

    image = load_rgb_image(image_bytes)
    processor = get_processor()
    inputs = processor(images=image, return_tensors="pt")

    with torch.inference_mode():
        logits = _get_torch_model()(**inputs).logits.detach().cpu().numpy()

    return "pytorch", _format_predictions(logits, top_k)


def predict_from_bytes(image_bytes: bytes, top_k: int = 5) -> dict[str, Any]:
    if settings.quantized_model_path.exists() or settings.onnx_model_path.exists():
        runtime, predictions = _predict_onnx(image_bytes, top_k)
    else:
        runtime, predictions = _predict_torch(image_bytes, top_k)

    return {
        "model": settings.model_id,
        "runtime": runtime,
        "top_k": top_k,
        "predictions": predictions,
    }
