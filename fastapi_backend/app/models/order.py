from datetime import datetime
from enum import Enum

from sqlalchemy import Column, Integer, String, DateTime, Numeric, JSON, ForeignKey
from app.database import Base


class OrderStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    RETURN_REQUESTED = "return_requested"


class Order(Base):
    __tablename__ = "orders"

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

    products = Column(
        JSON,
        nullable=False
    )

    total = Column(
        Numeric(10, 2),
        nullable=False
    )

    payment_status = Column(
        String(50),
        default="pending",
        nullable=False
    )

    order_status = Column(
        String(20),
        default=OrderStatus.PENDING.value,
        nullable=False
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    delivered_at = Column(
        DateTime,
        nullable=True
    )