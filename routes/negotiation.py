"""
Negotiation routes — endpoint to trigger a freight negotiation call.
"""
from model.dispatch.schemas import (
    NegotiationPayload, 
    DispatchResponse
)
from model.dispatch.dispatch import NegotiationDispatcher

from fastapi import (
    APIRouter, 
    HTTPException, 
    status
)

router = APIRouter(prefix="/negotiation", tags=["Negotiation"])

@router.post(
    "/dispatch",
    response_model=DispatchResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Dispatch a negotiation call",
    description=(
        "Creates a LiveKit room and dispatches the negotiator voice agent "
        "with the full freight and carrier payload as call metadata."
    ),
)
async def dispatch_negotiation(payload: NegotiationPayload) -> DispatchResponse:
    """
    Receives freight + carrier data, spins up a LiveKit room, and dispatches
    the negotiator agent. Returns the room and dispatch identifiers.
    """
    try:
        dispatcher = NegotiationDispatcher()
        return await dispatcher.dispatch(payload)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to dispatch negotiation: {e}",
        )
