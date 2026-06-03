from typing import Optional
from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    hashed_password: str
    role: str = Field(default="user")
    employee_id: Optional[str] = Field(default=None)


class ConversationMessage(SQLModel, table=True):
    """Persisted chat message."""

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(index=True)
    role: str
    content: str
    timestamp: str


class AuditLog(SQLModel, table=True):
    """Audit trail for system actions."""

    id: Optional[int] = Field(default=None, primary_key=True)
    actor_id: str = Field(index=True)
    action: str
    target: str = Field(default="")
    detail: str = Field(default="")
    timestamp: str = Field(index=True)
