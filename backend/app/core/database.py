from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings

# Connection configuration based on database dialect
is_sqlite = settings.sync_database_url.startswith("sqlite")

connect_args = (
    {"check_same_thread": False}
    if is_sqlite
    else {}
)

engine_kwargs = {
    "connect_args": connect_args,
    "pool_pre_ping": True,
}

# PostgreSQL production connection pooling
if not is_sqlite:
    engine_kwargs.update({
        "pool_size": 10,
        "max_overflow": 20,
        "pool_recycle": 1800,
    })

engine = create_engine(
    settings.sync_database_url,
    **engine_kwargs,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Declarative base for all SQLAlchemy models."""
    pass


def get_db():
    """
    FastAPI dependency that provides a SQLAlchemy database session.
    Ensures the session is always closed after use.
    """
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
