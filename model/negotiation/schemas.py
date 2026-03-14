"""
Negotiation Pydantic schemas — used in API responses and SSE status events.
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


class NegotiationRead(BaseModel):
    id: int
    call_id: str
    call_sid: Optional[str] = None

    carrier_name: Optional[str] = None
    carrier_phone: Optional[str] = None

    pickup_city: Optional[str] = None
    pickup_state: Optional[str] = None
    pickup_country: Optional[str] = None
    dropoff_city: Optional[str] = None
    dropoff_state: Optional[str] = None
    dropoff_country: Optional[str] = None
    trailer_type: Optional[str] = None
    distance: Optional[str] = None
    load_date: Optional[str] = None

    ai_price: Decimal
    max_price: Decimal
    final_price: Optional[Decimal] = None

    status: str
    reject_reason: Optional[str] = None
    language: Optional[str] = None

    created_at: Optional[datetime] = None
    answered_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class NegotiationStatusEvent(BaseModel):
    """Emitted as an SSE 'status' event whenever the negotiation status changes."""

    status: str
    final_price: Optional[Decimal] = None
    reject_reason: Optional[str] = None
