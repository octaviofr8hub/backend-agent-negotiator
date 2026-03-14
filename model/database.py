"""
SQLAlchemy engine, session factory, and declarative base.
All models import Base from here to share the same metadata.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Session


class Base(DeclarativeBase):
    pass


_engine = None


def get_engine():
    global _engine
    if _engine is None:
        from model.config import settings

        _engine = create_engine(
            str(settings.SQLALCHEMY_DATABASE_URI),
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
        )
    return _engine


def get_db() -> Session:
    factory = sessionmaker(bind=get_engine(), autocommit=False, autoflush=False)
    return factory()
