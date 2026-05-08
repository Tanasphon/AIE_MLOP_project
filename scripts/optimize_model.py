import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import onnxruntime as ort
import requests
import torch
from onnxruntime.quantization import QuantType, quantize_dynamic
from PIL import Image
from transformers import AutoImageProcessor, AutoModelForImageClassification


MODEL_ID = "apple/mobilevit-small"
ROOT_DIR = Path(__file__).resolve().parents[1]
MODELS_DIR = ROOT_DIR / "models"
ONNX_DIR = MODELS_DIR / "onnx"
QUANTIZED_DIR = MODELS_DIR / "quantized"
RESULTS_PATH = MODELS_DIR / "benchmark_results.json"


def download_sample_image(output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists():
        return output_path

    url = "https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/cats.png"
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    output_path.write_bytes(response.content)
    return output_path


def file_size_mb(path: Path) -> float:
    return round(path.stat().st_size / (1024 * 1024), 2)


def directory_size_mb(path: Path) -> float:
    total = sum(file.stat().st_size for file in path.rglob("*") if file.is_file())
    return round(total / (1024 * 1024), 2)


def percentile(values: list[float], pct: int) -> float:
    return round(float(np.percentile(values, pct)), 2)


def benchmark_torch(image_path: Path, runs: int) -> dict:
    processor = AutoImageProcessor.from_pretrained(MODEL_ID)
    model = AutoModelForImageClassification.from_pretrained(MODEL_ID)
    model.eval()
    image = Image.open(image_path).convert("RGB")
    inputs = processor(images=image, return_tensors="pt")

    for _ in range(3):
        with torch.inference_mode():
            model(**inputs)

    latencies = []
    for _ in range(runs):
        start = time.perf_counter()
        with torch.inference_mode():
            model(**inputs)
        latencies.append((time.perf_counter() - start) * 1000)

    model.save_pretrained(MODELS_DIR / "original")
    processor.save_pretrained(MODELS_DIR / "original")
    return {
        "runtime": "pytorch",
        "model_size_mb": directory_size_mb(MODELS_DIR / "original"),
        "latency_avg_ms": round(float(np.mean(latencies)), 2),
        "latency_p95_ms": percentile(latencies, 95),
    }


def export_onnx() -> Path:
    ONNX_DIR.mkdir(parents=True, exist_ok=True)
    model_path = ONNX_DIR / "model.onnx"
    if model_path.exists():
        return model_path

    subprocess.run(
        [
            sys.executable,
            "-m",
            "optimum.exporters.onnx",
            "--model",
            MODEL_ID,
            "--task",
            "image-classification",
            str(ONNX_DIR),
        ],
        check=True,
    )
    return model_path


def quantize_onnx(onnx_path: Path) -> Path:
    QUANTIZED_DIR.mkdir(parents=True, exist_ok=True)
    quantized_path = QUANTIZED_DIR / "model_quantized.onnx"
    quantize_dynamic(
        model_input=str(onnx_path),
        model_output=str(quantized_path),
        op_types_to_quantize=["MatMul", "Gemm"],
        weight_type=QuantType.QInt8,
    )
    return quantized_path


def benchmark_onnx(model_path: Path, image_path: Path, runs: int, runtime: str) -> dict:
    processor = AutoImageProcessor.from_pretrained(MODEL_ID)
    image = Image.open(image_path).convert("RGB")
    inputs = processor(images=image, return_tensors="np")
    session = ort.InferenceSession(str(model_path), providers=["CPUExecutionProvider"])
    input_name = session.get_inputs()[0].name

    for _ in range(3):
        session.run(None, {input_name: inputs["pixel_values"]})

    latencies = []
    for _ in range(runs):
        start = time.perf_counter()
        session.run(None, {input_name: inputs["pixel_values"]})
        latencies.append((time.perf_counter() - start) * 1000)

    return {
        "runtime": runtime,
        "model_size_mb": file_size_mb(model_path),
        "latency_avg_ms": round(float(np.mean(latencies)), 2),
        "latency_p95_ms": percentile(latencies, 95),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", type=int, default=20)
    parser.add_argument(
        "--image",
        type=Path,
        default=ROOT_DIR / "sample_images" / "benchmark.png",
    )
    args = parser.parse_args()

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    image_path = download_sample_image(args.image)
    onnx_path = export_onnx()
    quantized_path = quantize_onnx(onnx_path)

    results = {
        "model_id": MODEL_ID,
        "sample_image": str(image_path.relative_to(ROOT_DIR)),
        "runs": args.runs,
        "results": [
            benchmark_torch(image_path, args.runs),
            benchmark_onnx(onnx_path, image_path, args.runs, "onnx"),
            benchmark_onnx(quantized_path, image_path, args.runs, "onnx-quantized"),
        ],
    }
    RESULTS_PATH.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
