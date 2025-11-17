from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol, Dict, Any
from ..core.config import settings
import uuid


class PaymentProvider(Protocol):
    # PUBLIC_INTERFACE
    def create_session(self, user_id: str, book_id: str, amount_cents: int, currency: str) -> Dict[str, Any]:
        """Create a payment session/order and return client payload."""

    # PUBLIC_INTERFACE
    def verify_webhook(self, payload: bytes, headers: Dict[str, str]) -> Dict[str, Any]:
        """Verify webhook signature and return event dict."""


@dataclass
class MockProvider(PaymentProvider):
    def create_session(self, user_id: str, book_id: str, amount_cents: int, currency: str) -> Dict[str, Any]:
        return {
            "provider": "mock",
            "session_id": str(uuid.uuid4()),
            "amount_cents": amount_cents,
            "currency": currency,
            "status": "created",
        }

    def verify_webhook(self, payload: bytes, headers: Dict[str, str]) -> Dict[str, Any]:
        return {"type": "payment.succeeded", "data": {"transaction_id": str(uuid.uuid4())}}


@dataclass
class StripeProvider(PaymentProvider):
    secret_key: str
    webhook_secret: str | None = None

    def create_session(self, user_id: str, book_id: str, amount_cents: int, currency: str) -> Dict[str, Any]:
        # Placeholder; integrate stripe SDK in production
        return {"provider": "stripe", "checkout_url": "https://stripe.example/checkout", "amount_cents": amount_cents, "currency": currency}

    def verify_webhook(self, payload: bytes, headers: Dict[str, str]) -> Dict[str, Any]:
        # Placeholder signature verification
        return {"type": "payment_intent.succeeded", "data": {"id": str(uuid.uuid4())}}


@dataclass
class RazorpayProvider(PaymentProvider):
    key_id: str
    key_secret: str
    webhook_secret: str | None = None

    def create_session(self, user_id: str, book_id: str, amount_cents: int, currency: str) -> Dict[str, Any]:
        return {"provider": "razorpay", "order_id": str(uuid.uuid4()), "amount_cents": amount_cents, "currency": currency}

    def verify_webhook(self, payload: bytes, headers: Dict[str, str]) -> Dict[str, Any]:
        return {"event": "payment.captured", "payload": {"payment": {"entity": {"id": str(uuid.uuid4())}}}}


# PUBLIC_INTERFACE
def get_payment_provider() -> PaymentProvider:
    """Return active payment provider based on settings."""
    p = settings.PAYMENT_PROVIDER.lower()
    if p == "stripe" and settings.STRIPE_SECRET_KEY:
        return StripeProvider(secret_key=settings.STRIPE_SECRET_KEY, webhook_secret=settings.STRIPE_WEBHOOK_SECRET)
    if p == "razorpay" and settings.RAZORPAY_KEY_ID and settings.RAZORPAY_KEY_SECRET:
        return RazorpayProvider(
            key_id=settings.RAZORPAY_KEY_ID,
            key_secret=settings.RAZORPAY_KEY_SECRET,
            webhook_secret=settings.RAZORPAY_WEBHOOK_SECRET,
        )
    return MockProvider()
