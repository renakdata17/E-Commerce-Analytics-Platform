from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field, PositiveInt, field_validator


class CheckoutLine(BaseModel):
    sku: str = Field(min_length=4, max_length=64)
    qty: PositiveInt


class CheckoutRequest(BaseModel):
    email: EmailStr
    currency: str = Field(default="USD", min_length=3, max_length=3)

    lines: list[CheckoutLine]


class CheckoutResponse(BaseModel):
    order_id: str
    status: str
    total_cents: int


class ClickEventIngest(BaseModel):
    visitor_id: str
    session_id: str
    sku: str
    referrer: str | None = None
    millis_on_page_hint: int = Field(default=120, ge=0)

    @field_validator("visitor_id")
    @classmethod
    def strip_ids(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            msg = "visitor_id required"
            raise ValueError(msg)
        return cleaned


class ClickBatchRequest(BaseModel):
    events: list[ClickEventIngest]
