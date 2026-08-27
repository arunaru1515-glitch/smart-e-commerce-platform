from logging.config import fileConfig

from sqlalchemy import create_engine
from sqlalchemy import pool

from alembic import context

from app.database import Base, DATABASE_URL

# Import all models so Alembic can detect them
from app.models.user import User
from app.models.product import Product
from app.models.cart import Cart
from app.models.cart_item import CartItem
from app.models.order import Order
from app.models.payment import Payment
from app.models.notification import Notification


# ============================================================
# ALEMBIC CONFIGURATION
# ============================================================

config = context.config


# ============================================================
# LOGGING
# ============================================================

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


# ============================================================
# DATABASE URL
# ============================================================

config.set_main_option(
    "sqlalchemy.url",
    DATABASE_URL
)


# ============================================================
# SQLALCHEMY MODEL METADATA
# ============================================================

target_metadata = Base.metadata


# ============================================================
# IGNORE UNRELATED EXISTING TABLES
# ============================================================

def include_object(
    object,
    name,
    type_,
    reflected,
    compare_to
):
    """
    Prevent Alembic from trying to delete existing database
    tables that are not part of the FastAPI SQLAlchemy models.
    """

    if type_ == "table" and reflected and compare_to is None:
        return False

    return True


# ============================================================
# OFFLINE MIGRATIONS
# ============================================================

def run_migrations_offline() -> None:
    """Run migrations in offline mode."""

    url = config.get_main_option(
        "sqlalchemy.url"
    )

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={
            "paramstyle": "named"
        },
        include_object=include_object,
    )

    with context.begin_transaction():
        context.run_migrations()


# ============================================================
# ONLINE MIGRATIONS
# ============================================================

def run_migrations_online() -> None:
    """Run migrations in online mode."""

    connectable = create_engine(
        DATABASE_URL,
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:

        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=include_object,
        )

        with context.begin_transaction():
            context.run_migrations()


# ============================================================
# RUN MIGRATION
# ============================================================

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()