"""
Dispatch — Creates a LiveKit room and dispatches the negotiator voice agent.

Flow: create room → dispatch agent with payload as metadata → return identifiers.
"""
from model.config import settings
from model.dispatch.schemas import (
    NegotiationPayload, 
    DispatchResponse
)

import json
import uuid
import logging
from livekit import api



logger = logging.getLogger("dispatch")


class NegotiationDispatcher:
    """Handles LiveKit room creation and negotiator agent dispatch."""

    AGENT_NAME = "negotiator-agent"

    def __init__(self) -> None:
        self._lk = api.LiveKitAPI(
            settings.LIVEKIT_URL,
            settings.LIVEKIT_API_KEY,
            settings.LIVEKIT_API_SECRET,
        )

    async def dispatch(self, payload: NegotiationPayload) -> DispatchResponse:
        """
        Creates a LiveKit room and dispatches the negotiator voice agent.

        The full NegotiationPayload is serialised as JSON and forwarded to the
        agent via the dispatch metadata field so it has all context for the call.

        Args:
            payload: Validated freight + carrier data for the negotiation.

        Returns:
            DispatchResponse with room_name, room_sid, and dispatch_id.

        Raises:
            Exception: If room creation or agent dispatch fails.
        """
        room_name = (
            f"negotiation-{payload.carrier_main_phone.replace('+', '')}"
            f"-{uuid.uuid4().hex[:8]}"
        )

        try:
            # 1. Create the room
            logger.info(f"[DISPATCH] Creating room: {room_name} for carrier '{payload.carrier_name}'")
            room = await self._lk.room.create_room(
                api.CreateRoomRequest(
                    name=room_name,
                    empty_timeout=300,  # Auto-close after 5 min with no participants
                )
            )
            logger.info(f"[DISPATCH] Room created: {room.name} (sid: {room.sid})")

            # 2. Dispatch the negotiator agent
            logger.info(f"[DISPATCH] Dispatching '{self.AGENT_NAME}' to room: {room.name}")
            dispatch = await self._lk.agent_dispatch.create_dispatch(
                api.CreateAgentDispatchRequest(
                    agent_name=self.AGENT_NAME,
                    room=room.name,
                    metadata=json.dumps(payload.model_dump()),
                )
            )

            dispatch_id = getattr(dispatch, "id", getattr(dispatch, "dispatch_id", "unknown"))
            logger.info(f"[DISPATCH] Agent dispatched | dispatch_id={dispatch_id}")

            return DispatchResponse(
                room_name=room.name,
                room_sid=room.sid,
                dispatch_id=dispatch_id,
            )

        except Exception as e:
            logger.error(f"[DISPATCH] Failed for room '{room_name}': {e}")
            raise

        finally:
            await self._lk.aclose()
