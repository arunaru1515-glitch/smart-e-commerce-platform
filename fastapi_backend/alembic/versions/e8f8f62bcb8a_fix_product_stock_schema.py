"""fix product stock schema

Revision ID: e8f8f62bcb8a
Revises: 4b83569a634f
Create Date: 2026-08-27 23:06:25.208387

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


# ============================================================
# REVISION IDENTIFIERS
# ============================================================

revision: str = "e8f8f62bcb8a"
down_revision: Union[str, Sequence[str], None] = "4b83569a634f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# ============================================================
# UPGRADE
# ============================================================

def upgrade() -> None:
    """
    Fix the products table schema.

    The old database may contain both:
        stock
        stock_quantity

    The application now uses stock_quantity.

    Existing stock values are copied to stock_quantity
    before the old stock column is removed.
    """

    # --------------------------------------------------------
    # 1. Copy old stock values into stock_quantity
    # --------------------------------------------------------

    op.execute(
        """
        UPDATE products
        SET stock_quantity = stock
        WHERE stock_quantity IS NULL
        """
    )

    # --------------------------------------------------------
    # 2. Remove the old stock column
    # --------------------------------------------------------

    op.drop_column(
        "products",
        "stock"
    )


# ============================================================
# DOWNGRADE
# ============================================================

def downgrade() -> None:
    """
    Restore the old stock column if migration is reversed.
    """

    # --------------------------------------------------------
    # 1. Re-create old stock column
    # --------------------------------------------------------

    op.add_column(
        "products",
        sa.Column(
            "stock",
            mysql.INTEGER(),
            nullable=True
        )
    )

    # --------------------------------------------------------
    # 2. Copy stock_quantity back to stock
    # --------------------------------------------------------

    op.execute(
        """
        UPDATE products
        SET stock = stock_quantity
        WHERE stock IS NULL
        """
    )