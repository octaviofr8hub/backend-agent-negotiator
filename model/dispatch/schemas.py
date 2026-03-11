"""
Negotiation schemas — Pydantic models for the freight negotiation payload
and the dispatch response.
"""
from pydantic import BaseModel, Field

class NegotiationPayload(BaseModel):
    """
    All the freight + carrier data that gets sent to the voice agent
    as call metadata when a negotiation room is created.
    """
    # ── Load details ──
    trailer_type: str = Field(..., examples=["dry_van"])
    date: str = Field(..., examples=["2024-07-01"])
    distance: float = Field(..., gt=0, description="Route distance (miles)")
    ai_price: float = Field(..., gt=0, description="AI suggested rate (USD)")
    # ── Origin ──
    pickup_city: str
    pickup_state: str
    pickup_country: str
    # ── Destination ──
    dropoff_city: str
    dropoff_state: str
    dropoff_country: str
    # ── Carrier contact ──
    carrier_name: str
    carrier_main_email: str
    carrier_main_phone: str

class DispatchResponse(BaseModel):
    """Returned after the LiveKit room is created and the agent is dispatched."""
    room_name: str
    room_sid: str
    dispatch_id: str
