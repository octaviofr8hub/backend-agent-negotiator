"""
TranscriptMessage Pydantic schemas — used in SSE message events.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class TranscriptMessageRead(BaseModel):
    """A single message from the conversation transcript."""

    id: int
    negotiation_id: int
    role: str           # user | assistant | tool
    content: str
    tool_name: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class TranscriptStreamConnected(BaseModel):
    """Emitted as the first SSE event when the stream is established."""

    call_id: str
    status: str
    last_message_id: int
