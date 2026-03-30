"""Pydantic schemas untuk analysis endpoints."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class AIAnalysisResponse(BaseModel):
    id: int
    stock_id: int
    summary: str
    recommendation: str
    valuation_analysis: str | None = None
    quality_analysis: str | None = None
    momentum_analysis: str | None = None
    supporting_factors: list[Any] | None = None
    data_sufficiency: bool
    missing_data_info: str | None = None
    model_used: str | None = None
    prompt_version: str | None = None
    generated_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}


class AIAnalysisRefreshResponse(BaseModel):
    message: str
    stock_code: str
