from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends, Query, Header
from typing import Optional
from datetime import date, timedelta
from sqlalchemy.orm import Session
from ...db.session import SessionLocal
from ...models.purchase import Purchase
from ...models.book import Book
from ...models.user import User
from sqlalchemy import func, desc
from ...services.auth_service import get_token_payload

router = APIRouter()

def _get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def _admin_required(authorization: Optional[str] = Header(None), db: Session = Depends(_get_db)):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = authorization.split(" ", 1)[1]
    try:
        claims = get_token_payload(token, expected_type="access")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = db.query(User).filter(User.id == claims["sub"]).first()
    if not user or not getattr(user, "is_superuser", False):
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

@router.get("/stats/sales_by_day", summary="Sales by day", description="Daily sales counts and revenue.", tags=["Admin"])
def sales_by_day(days: int = Query(7, ge=1, le=90), admin=Depends(_admin_required), db: Session = Depends(_get_db)):
    end = date.today()
    start = end - timedelta(days=days - 1)
    rows = (
        db.query(func.date(Purchase.created_at).label("d"), func.count(Purchase.id), func.sum(Purchase.price_cents))
        .filter(Purchase.created_at >= start)
        .group_by(func.date(Purchase.created_at))
        .order_by(func.date(Purchase.created_at))
        .all()
    )
    return [{"date": str(r[0]), "count": int(r[1] or 0), "revenue_cents": int(r[2] or 0)} for r in rows]

@router.get("/stats/top_books", summary="Top books", description="Top selling books by count.", tags=["Admin"])
def top_books(limit: int = Query(5, ge=1, le=50), admin=Depends(_admin_required), db: Session = Depends(_get_db)):
    rows = (
        db.query(Book.title, func.count(Purchase.id).label("cnt"))
        .join(Purchase, Purchase.book_id == Book.id)
        .group_by(Book.id)
        .order_by(desc("cnt"))
        .limit(limit)
        .all()
    )
    return [{"title": r[0], "count": int(r[1])} for r in rows]

@router.get("/stats/summary", summary="Summary metrics", description="Revenue and user counts.", tags=["Admin"])
def summary(admin=Depends(_admin_required), db: Session = Depends(_get_db)):
    revenue = db.query(func.coalesce(func.sum(Purchase.price_cents), 0)).scalar() or 0
    users = db.query(func.count(User.id)).scalar() or 0
    return {"revenue_cents": int(revenue), "users": int(users)}
