"""SQLAlchemy database setup with synchronous SQLite engine."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from typing import Generator

from app.config import get_settings

settings = get_settings()

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """Yield a database session, ensuring it is closed after use.

    Usage as a FastAPI dependency:
        db: Session = Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all tables defined by ORM models.

    Must be called after all models have been imported so that
    ``Base.metadata`` contains their table definitions.
    """
    import app.models  # noqa: F401 — ensure models are registered
    Base.metadata.create_all(bind=engine)
