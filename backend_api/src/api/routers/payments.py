from __future__ import annotations
from typing import Optional

from fastapi import APIRouter, HTTPException, Request, Depends, Header
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.services.payments_service import get_payment_provider
from src.services.auth_service import get_token_payload
from src.db.session import get_db
from src.models.purchase import Purchase
from src.models.book import Book

router = APIRouter()


def _auth_required(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = authorization.split(" ", 1)[1]
    try:
        return get_token_payload(token, expected_type="access")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")


class PaymentInitRequest(BaseModel):
    book_id: str = Field(..., description="Book ID to purchase")
    currency: Optional[str] = Field(None, description="Currency code, defaults to backend setting")


class PaymentInitResponse(BaseModel):
    provider: str
    data: dict


@router.post(
    "/init",
    response_model=PaymentInitResponse,
    summary="Create payment session",
    description="Initialize a payment session for purchasing a book.",
    tags=["Payments"],
)
def create_payment_session(req: PaymentInitRequest, auth=Depends(_auth_required), db: Session = Depends(get_db)):
    user_id = auth["sub"]
    book = db.query(Book).filter(Book.id == req.book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    amount_cents = book.price_cents or 0
    currency = req.currency or book.currency or "USD"

    provider = get_payment_provider()
    session_data = provider.create_session(user_id=user_id, book_id=book.id, amount_cents=amount_cents, currency=currency)
    return PaymentInitResponse(provider=session_data.get("provider", "mock"), data=session_data)


@router.post(
    "/webhook",
    status_code=200,
    summary="Payment webhook",
    description="Receive payment provider webhooks to confirm payments and create purchases.",
    tags=["Payments"],
)
async def payment_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.body()
    headers = {k: v for k, v in request.headers.items()}
    provider = get_payment_provider()
    event = provider.verify_webhook(payload, headers)

    # Map generic success event to transaction id
    transaction_id = None
    if "data" in event and isinstance(event["data"], dict):
        transaction_id = event["data"].get("id") or event["data"].get("transaction_id")
    elif "payload" in event:
        # razorpay-like
        transaction_id = event["payload"].get("payment", {}).get("entity", {}).get("id") if isinstance(event["payload"], dict) else None

    if not transaction_id:
        return {"status": "ignored"}

    # Idempotent: check existing
    existing = db.query(Purchase).filter(Purchase.transaction_id == transaction_id).first()
    if existing:
        return {"status": "ok", "purchase_id": str(existing.id)}

    # For mock provider we cannot infer book/user from payload; skipping here.
    # In real providers include metadata in session creation and propagate to webhook.
    # Create a placeholder completed purchase if applicable (no-op here).
    return {"status": "ok"}
