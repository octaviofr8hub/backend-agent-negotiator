"""
Transcript routes — real-time SSE stream of a negotiation conversation.
"""
import logging
from typing import AsyncGenerator

from fastapi import APIRouter, Query, Request
from fastapi.responses import StreamingResponse

from model.negotiation.schemas import NegotiationRead
from model.transcript.schemas import TranscriptMessageRead, TranscriptStreamConnected
from model.negotiation.schemas import NegotiationStatusEvent
from services.transcript_stream import stream_transcript

logger = logging.getLogger("routes.transcript")

router = APIRouter(prefix="/transcript", tags=["Transcript"])


@router.get(
    "/{call_id}/stream",
    summary="Stream transcript in real time (SSE)",
    description=(
        "Opens a Server-Sent Events stream for the given negotiation call_id. "
        "The client receives new transcript messages and status changes as they "
        "are written to the database by the worker agent — no polling required.\n\n"
        "**SSE event types:**\n"
        "- `connected` — stream established, carries current status and last message id\n"
        "- *(default)* — new `TranscriptMessageRead` JSON object\n"
        "- `status` — `NegotiationStatusEvent` JSON when the negotiation status changes\n"
        "- `done` — terminal status reached; stream closes automatically\n"
        "- `error` — negotiation not found or unexpected error\n\n"
        "Pass `?since_id=<id>` to resume from a specific message after a reconnect."
    ),
    response_class=StreamingResponse,
    responses={
        200: {
            "content": {"text/event-stream": {}},
            "description": "SSE stream of transcript events",
        }
    },
)
async def transcript_stream(
    call_id: str,
    request: Request,
    since_id: int = Query(0, ge=0, description="Resume stream after this message id"),
) -> StreamingResponse:
    """
    Returns a StreamingResponse (text/event-stream) that pushes new transcript
    messages and status changes to the client as they occur.
    """

    async def event_generator() -> AsyncGenerator[str, None]:
        try:
            async for chunk in stream_transcript(call_id, since_id):
                if await request.is_disconnected():
                    logger.info("[SSE] Client disconnected from %s", call_id)
                    break
                yield chunk
        except Exception as exc:
            logger.exception("[SSE] Unexpected error streaming %s: %s", call_id, exc)
            import json
            yield f"event: error\ndata: {json.dumps({'detail': str(exc)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",   # Disable Nginx buffering
            "Connection": "keep-alive",
        },
    )


@router.get(
    "/{call_id}",
    summary="Get negotiation details",
    response_model=NegotiationRead,
    description="Returns the current negotiation record for the given call_id.",
)
async def get_negotiation(call_id: str) -> NegotiationRead:
    """Fetch a single negotiation by call_id (synchronous snapshot)."""
    import asyncio
    from sqlalchemy import select
    from model.database import get_db
    from model.negotiation.model import Negotiation
    from fastapi import HTTPException, status

    loop = asyncio.get_running_loop()

    def _fetch():
        db = get_db()
        try:
            return db.execute(
                select(Negotiation).where(Negotiation.call_id == call_id)
            ).scalar_one_or_none()
        finally:
            db.close()

    neg = await loop.run_in_executor(None, _fetch)

    if neg is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Negotiation '{call_id}' not found",
        )

    return NegotiationRead.model_validate(neg)
