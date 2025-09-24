import os
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def _db_url_from_env() -> str:
    # Prefer a full URL if provided
    url = os.getenv("DATABASE_URL")
    if url:
        return url

    # Build from discrete vars, defaults align with docker-compose.yml
    user = os.getenv("DB_USER", "postgres")
    password = os.getenv("DB_PASSWORD", os.getenv("POSTGRES_DB_PASSWORD", ""))
    host = os.getenv("DB_HOST", "db")
    port = os.getenv("DB_PORT", "5432")
    name = os.getenv("DB_NAME", os.getenv("POSTGRES_DB", "db"))
    return f"postgresql+psycopg://{user}:{password}@{host}:{port}/{name}"


def get_engine(echo: bool = False):
    return create_engine(_db_url_from_env(), echo=echo, pool_pre_ping=True, future=True)


def get_sessionmaker(echo: bool = False):
    engine = get_engine(echo=echo)
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)


@contextmanager
def session_scope(echo: bool = False):
    """Provide a transactional scope around a series of operations."""
    Session = get_sessionmaker(echo=echo)
    session = Session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

