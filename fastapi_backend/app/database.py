from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# MySQL database connection
DATABASE_URL = "mysql+pymysql://root:811008@localhost:3306/ecommerce_db"

# Create database engine
engine = create_engine(
    DATABASE_URL,
    echo=True
)

# Create database session
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base class for database models
Base = declarative_base()


# Database connection dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()