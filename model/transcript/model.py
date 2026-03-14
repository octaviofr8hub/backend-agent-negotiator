"""
TranscriptMessage — read-only SQLAlchemy model mirroring the worker-agent-negotiator DB.
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship

from model.database import Base


class TranscriptMessage(Base):
    __tablename__ = "transcript_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    negotiation_id = Column(
        Integer,
        ForeignKey("negotiations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role = Column(String(20), nullable=False)  # user | assistant | tool
    content = Column(Text, nullable=False)
    tool_name = Column(String(50))
    created_at = Column(DateTime(timezone=True))

    negotiation = relationship("Negotiation", back_populates="messages")
