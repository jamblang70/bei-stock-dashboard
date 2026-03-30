"""Pydantic schemas for watchlist endpoints."""

from datetime import datetime

from pydantic import BaseModel, Field


class WatchlistAddRequest(BaseModel):
    code: str = Field(..., min_length=1, max_length=10, description="Stock code to add")


class WatchlistItem(BaseModel):
    code: str
    name: str
    sector: str | None = None
    price: float | None = None
    change_pct: float | None = None
    score: float | None = None
    recommendation: str | None = None
    added_at: datetime


class WatchlistResponse(BaseModel):
    data: list[WatchlistItem]
    total: int


class MessageResponse(BaseModel):
    message: str
