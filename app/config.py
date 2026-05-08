import os
from pathlib import Path

from pydantic import BaseModel, Field


class Settings(BaseModel):
    app_name: str = "MobileViT Image Classification API"
    model_id: str = "apple/mobilevit-small"
    model_dir: Path = Path(os.getenv("MODEL_DIR", "models"))
    max_upload_bytes: int = Field(
        default=int(os.getenv("MAX_UPLOAD_BYTES", str(5 * 1024 * 1024))),
        gt=0,
    )
    max_workers: int = Field(default=int(os.getenv("MAX_WORKERS", "2")), gt=0)

    @property
    def onnx_model_path(self) -> Path:
        return self.model_dir / "onnx" / "model.onnx"

    @property
    def quantized_model_path(self) -> Path:
        return self.model_dir / "quantized" / "model_quantized.onnx"


settings = Settings()
