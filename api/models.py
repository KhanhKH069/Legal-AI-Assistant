from typing import Optional
from sqlmodel import Field, SQLModel


class ConversationMessage(SQLModel, table=True):
    """Persisted chat message."""

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(index=True)
    role: str  # "user" | "assistant"
    content: str
    timestamp: str  # ISO datetime string


class AuditLog(SQLModel, table=True):
    """Audit trail for system actions."""

    id: Optional[int] = Field(default=None, primary_key=True)
    actor_id: str = Field(index=True)  # who performed the action
    action: str  # e.g. "VIEW_DOCUMENT", "UPLOAD_CONTRACT"
    target: str = Field(default="")
    detail: str = Field(default="")  # extra context
    timestamp: str = Field(index=True)  # ISO datetime string
