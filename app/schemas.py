from pydantic import BaseModel, Field


class PredictionItem(BaseModel):
    label: str
    score: float = Field(ge=0.0, le=1.0)


class PredictionResponse(BaseModel):
    model: str
    runtime: str
    top_k: int
    predictions: list[PredictionItem]


class HealthResponse(BaseModel):
    status: str
    model: str


class ErrorResponse(BaseModel):
    detail: str
