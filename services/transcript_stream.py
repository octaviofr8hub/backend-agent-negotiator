"""
Transcript stream — async SSE generator that polls the DB for new transcript
messages and status changes on a live negotiation.

Design:
  - One fresh DB session per poll cycle (thread-safe, avoids stale caches).
  - Runs sync SQLAlchemy queries in a thread-pool executor so the async loop
    is never blocked.
  - Emits four SSE event types:
      (no event field)  transcript message   →  TranscriptMessageRead JSON
      event: status     status change        →  NegotiationStatusEvent JSON
      event: done       terminal status      →  {"status": "<terminal>"}
      event: error      negotiation missing  →  {"detail": "..."}
"""
import asyncio
import json
import logging
from typing import AsyncGenerator

from sqlalchemy import select
from sqlalchemy.orm import Session

from model.database import get_db
from model.negotiation.model import Negotiation
from model.negotiation.schemas import NegotiationStatusEvent
from model.transcript.model import TranscriptMessage
from model.transcript.schemas import TranscriptMessageRead, TranscriptStreamConnected

logger = logging.getLogger("transcript_stream")

TERMINAL_STATUSES = frozenset({"accepted", "rejected", "unavailable", "ended", "error"})
POLL_INTERVAL = 1.0  # seconds between DB polls


# ── Sync helpers (run inside executor threads) ────────────────────────────────

def _poll(call_id: str, last_msg_id: int) -> dict | None:
    """
    Opens a fresh session, fetches the current negotiation state and any
    new transcript messages since `last_msg_id`.  Returns a plain dict so
    the ORM objects are fully resolved before the session closes.
    """
    db: Session = get_db()
    try:
        neg = db.execute(
            select(Negotiation).where(Negotiation.call_id == call_id)
        ).scalar_one_or_none()

        if neg is None:
            return None

        msgs = db.execute(
            select(TranscriptMessage)
            .where(TranscriptMessage.negotiation_id == neg.id)
            .where(TranscriptMessage.id > last_msg_id)
            .order_by(TranscriptMessage.id)
        ).scalars().all()

        return {
            "neg_id": neg.id,
            "status": neg.status,
            "final_price": str(neg.final_price) if neg.final_price is not None else None,
            "reject_reason": neg.reject_reason,
            "messages": [
                {
                    "id": m.id,
                    "negotiation_id": m.negotiation_id,
                    "role": m.role,
                    "content": m.content,
                    "tool_name": m.tool_name,
                    "created_at": m.created_at.isoformat() if m.created_at else None,
                }
                for m in msgs
            ],
        }
    finally:
        db.close()


# ── Public async generator ────────────────────────────────────────────────────

async def stream_transcript(
    call_id: str,
    since_id: int = 0,
) -> AsyncGenerator[str, None]:
    """
    Async generator that yields SSE-formatted strings.

    Args:
        call_id:  The negotiation call_id to stream.
        since_id: Resume from this message id (0 = from the beginning).
                  Useful when the client reconnects after a drop.
    """
    loop = asyncio.get_running_loop()
    last_id = since_id
    last_status: str | None = None

    # ── Initial probe ────────────────────────────────────────────────────────
    result = await loop.run_in_executor(None, _poll, call_id, last_id)

    if result is None:
        yield f"event: error\ndata: {json.dumps({'detail': 'Negotiation not found'})}\n\n"
        return

    last_status = result["status"]

    connected = TranscriptStreamConnected(
        call_id=call_id,
        status=last_status,
        last_message_id=last_id,
    )
    yield f"event: connected\ndata: {connected.model_dump_json()}\n\n"

    # Emit any messages that already exist (e.g. on reconnect with since_id=0)
    for raw in result["messages"]:
        msg = TranscriptMessageRead.model_validate(raw)
        yield f"data: {msg.model_dump_json()}\n\n"
        last_id = raw["id"]

    if last_status in TERMINAL_STATUSES:
        yield f"event: done\ndata: {json.dumps({'status': last_status})}\n\n"
        return

    # ── Polling loop ─────────────────────────────────────────────────────────
    while True:
        await asyncio.sleep(POLL_INTERVAL)

        result = await loop.run_in_executor(None, _poll, call_id, last_id)

        if result is None:
            logger.warning("[stream] Negotiation %s disappeared from DB", call_id)
            yield f"event: error\ndata: {json.dumps({'detail': 'Negotiation not found'})}\n\n"
            return

        # New transcript messages
        for raw in result["messages"]:
            msg = TranscriptMessageRead.model_validate(raw)
            yield f"data: {msg.model_dump_json()}\n\n"
            last_id = raw["id"]

        # Status change
        if result["status"] != last_status:
            last_status = result["status"]
            status_event = NegotiationStatusEvent(
                status=last_status,
                final_price=result["final_price"],
                reject_reason=result["reject_reason"],
            )
            yield f"event: status\ndata: {status_event.model_dump_json()}\n\n"
            logger.info("[stream] %s status → %s", call_id, last_status)

        # Terminal — close the stream
        if last_status in TERMINAL_STATUSES:
            yield f"event: done\ndata: {json.dumps({'status': last_status})}\n\n"
            logger.info("[stream] %s reached terminal status, closing stream", call_id)
            return
