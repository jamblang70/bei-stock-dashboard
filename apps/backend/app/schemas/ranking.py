"""Pydantic schemas for ranking endpoint."""

from pydantic import BaseModel


class RankingItem(BaseModel):
    code: str
    name: str
    sector: str | None = None
    last_price: float | None = None
    change_pct: float | None = None
    score: float | None = None
    per: float | None = None
    pbv: float | None = None
    roe: float | None = None
    dividend_yield: float | None = None
    recommendation: str | None = None
    is_syariah: bool | None = None


class RankingResponse(BaseModel):
    data: list[RankingItem]
    total: int
    page: int
    per_page: int
    total_pages: int
