from sqlalchemy import Column, Integer, String, Float, Boolean

from app.database import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    name = Column(
        String(255),
        nullable=False
    )

    description = Column(
        String(500),
        nullable=True
    )

    price = Column(
        Float,
        nullable=False
    )

    category = Column(
        String(100),
        nullable=False,
        index=True
    )

    popularity = Column(
        Integer,
        default=0
    )

    stock_quantity = Column(
        Integer,
        default=0
    )

    is_available = Column(
        Boolean,
        default=True
    )