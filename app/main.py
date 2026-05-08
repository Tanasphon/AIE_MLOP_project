from concurrent.futures import ProcessPoolExecutor
from contextlib import asynccontextmanager
from functools import partial

import asyncio
from fastapi import FastAPI, File, HTTPException, Query, UploadFile, status

from app.config import settings
from app.image_utils import validate_image_bytes, validate_upload_metadata
from app.model import predict_from_bytes
from app.schemas import ErrorResponse, HealthResponse, PredictionResponse


executor: ProcessPoolExecutor | None = None


@asynccontextmanager
async def lifespan(_: FastAPI):
    global executor
    executor = ProcessPoolExecutor(max_workers=settings.max_workers)
    yield
    executor.shutdown(wait=True, cancel_futures=True)


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    lifespan=lifespan,
)


async def run_prediction(image_bytes: bytes, top_k: int) -> dict:
    if executor is None:
        raise RuntimeError("Inference executor is not initialized.")

    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        executor,
        partial(predict_from_bytes, image_bytes=image_bytes, top_k=top_k),
    )


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok", model=settings.model_id)


@app.post(
    "/predict",
    response_model=PredictionResponse,
    responses={
        400: {"model": ErrorResponse},
        413: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
async def predict(
    file: UploadFile = File(...),
    top_k: int = Query(default=5, ge=1, le=10),
) -> PredictionResponse:
    validate_upload_metadata(file)
    image_bytes = validate_image_bytes(await file.read())

    try:
        result = await run_prediction(image_bytes, top_k)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction failed: {exc}",
        ) from exc

    return PredictionResponse(**result)
