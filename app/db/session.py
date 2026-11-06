from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings, normalize_database_url


def get_session_factory() -> sessionmaker[Session]:
    settings = get_settings()
    if settings.database_url.startswith("******"):
        raise RuntimeError(
            "DATABASE_URL is still a placeholder. "
            "Set a valid PostgreSQL URL in .env before using the database."
        )
    engine = create_engine(normalize_database_url(settings.database_url), pool_pre_ping=True)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db():
    db: Session = get_session_factory()()
    try:
        yield db
    finally:
        db.close()