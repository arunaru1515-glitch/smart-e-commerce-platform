from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
)

from app.database import Base


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    user = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    type = Column(
        String(100),
        nullable=False
    )

    message = Column(
        String(500),
        nullable=False
    )

    read_status = Column(
        String(20),
        default="unread",
        nullable=False
    )

    timestamp = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )