"""initial_schema

Revision ID: 4b83569a634f
Revises:
Create Date: 2026-08-27 20:46:40.734515

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


# ============================================================
# REVISION IDENTIFIERS
# ============================================================

revision: str = "4b83569a634f"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# ============================================================
# UPGRADE
# ============================================================

def upgrade() -> None:
    """Upgrade database schema."""

    # Products table changes

    op.alter_column(
        "products",
        "name",
        existing_type=mysql.VARCHAR(length=150),
        type_=sa.String(length=255),
        existing_nullable=False,
    )

    op.alter_column(
        "products",
        "description",
        existing_type=mysql.TEXT(),
        type_=sa.String(length=500),
        existing_nullable=True,
    )

    op.alter_column(
        "products",
        "popularity",
        existing_type=mysql.INTEGER(),
        nullable=True,
        existing_server_default=sa.text("'0'"),
    )

    op.alter_column(
        "products",
        "stock_quantity",
        existing_type=mysql.INTEGER(),
        nullable=True,
        existing_server_default=sa.text("'0'"),
    )

    op.alter_column(
        "products",
        "is_available",
        existing_type=mysql.TINYINT(display_width=1),
        nullable=True,
        existing_server_default=sa.text("'1'"),
    )

    # Add category index
    op.create_index(
        op.f("ix_products_category"),
        "products",
        ["category"],
        unique=False,
    )

    # NOTE:
    # The existing 'stock' column is intentionally NOT dropped.
    # Existing database data should not be deleted by this migration.


# ============================================================
# DOWNGRADE
# ============================================================

def downgrade() -> None:
    """Downgrade database schema."""

    # Remove category index
    op.drop_index(
        op.f("ix_products_category"),
        table_name="products",
    )

    op.alter_column(
        "products",
        "is_available",
        existing_type=mysql.TINYINT(display_width=1),
        nullable=False,
        existing_server_default=sa.text("'1'"),
    )

    op.alter_column(
        "products",
        "stock_quantity",
        existing_type=mysql.INTEGER(),
        nullable=False,
        existing_server_default=sa.text("'0'"),
    )

    op.alter_column(
        "products",
        "popularity",
        existing_type=mysql.INTEGER(),
        nullable=False,
        existing_server_default=sa.text("'0'"),
    )

    op.alter_column(
        "products",
        "description",
        existing_type=sa.String(length=500),
        type_=mysql.TEXT(),
        existing_nullable=True,
    )

    op.alter_column(
        "products",
        "name",
        existing_type=sa.String(length=255),
        type_=mysql.VARCHAR(length=150),
        existing_nullable=False,
    )