"""Watchlist API router — requires authentication."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.stock import Stock, StockPrice, StockScore
from app.models.user import User
from app.models.watchlist import Watchlist
from app.schemas.watchlist import MessageResponse, WatchlistAddRequest, WatchlistItem, WatchlistResponse
from app.services.auth_service import get_current_user_from_token

router = APIRouter()
_bearer = HTTPBearer()

MAX_WATCHLIST_SIZE = 50


# ---------------------------------------------------------------------------
# Auth dependency
# ---------------------------------------------------------------------------


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    """Decode Bearer token and return the current user."""
    return get_current_user_from_token(db, credentials.credentials)


# ---------------------------------------------------------------------------
# GET /
# ---------------------------------------------------------------------------


@router.get("/", response_model=WatchlistResponse)
def get_watchlist(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return the authenticated user's watchlist with latest price and score."""
    entries = (
        db.query(Watchlist)
        .filter(Watchlist.user_id == current_user.id)
        .order_by(Watchlist.added_at.desc())
        .all()
    )

    items: list[WatchlistItem] = []
    for entry in entries:
        stock: Stock = entry.stock

        # Latest price
        latest_price = (
            db.query(StockPrice)
            .filter(StockPrice.stock_id == stock.id)
            .order_by(StockPrice.recorded_at.desc())
            .first()
        )

        # Latest score
        latest_score = (
            db.query(StockScore)
            .filter(StockScore.stock_id == stock.id)
            .order_by(StockScore.calculated_at.desc())
            .first()
        )

        items.append(
            WatchlistItem(
                code=stock.code,
                name=stock.name,
                sector=stock.sector,
                price=float(latest_price.price) if latest_price else None,
                change_pct=float(latest_price.change_pct) if latest_price and latest_price.change_pct is not None else None,
                score=float(latest_score.score) if latest_score else None,
                recommendation=latest_score.recommendation if latest_score else None,
                added_at=entry.added_at,
            )
        )

    return WatchlistResponse(data=items, total=len(items))


# ---------------------------------------------------------------------------
# POST /
# ---------------------------------------------------------------------------


@router.post("/", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def add_to_watchlist(
    body: WatchlistAddRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Add a stock to the user's watchlist. Max 50 stocks, no duplicates."""
    # Validate stock exists
    stock = (
        db.query(Stock)
        .filter(Stock.code == body.code.upper(), Stock.is_active == True)  # noqa: E712
        .first()
    )
    if not stock:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Saham tidak ditemukan",
        )

    # Check duplicate
    existing = (
        db.query(Watchlist)
        .filter(Watchlist.user_id == current_user.id, Watchlist.stock_id == stock.id)
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Saham sudah ada di watchlist",
        )

    # Check max limit
    count = (
        db.query(Watchlist)
        .filter(Watchlist.user_id == current_user.id)
        .count()
    )
    if count >= MAX_WATCHLIST_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Watchlist sudah mencapai batas maksimum {MAX_WATCHLIST_SIZE} saham",
        )

    entry = Watchlist(user_id=current_user.id, stock_id=stock.id)
    db.add(entry)
    db.commit()

    return MessageResponse(message=f"{stock.code} berhasil ditambahkan ke watchlist")


# ---------------------------------------------------------------------------
# DELETE /{code}
# ---------------------------------------------------------------------------


@router.delete("/{code}", response_model=MessageResponse)
def remove_from_watchlist(
    code: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Remove a stock from the user's watchlist."""
    stock = db.query(Stock).filter(Stock.code == code.upper()).first()
    if not stock:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Saham tidak ditemukan",
        )

    entry = (
        db.query(Watchlist)
        .filter(Watchlist.user_id == current_user.id, Watchlist.stock_id == stock.id)
        .first()
    )
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Saham tidak ada di watchlist",
        )

    db.delete(entry)
    db.commit()

    return MessageResponse(message=f"{stock.code} berhasil dihapus dari watchlist")
