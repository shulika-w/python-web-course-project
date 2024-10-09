"""
Module with declaring of connections to PostgreSQL and Redis
"""


from fastapi import HTTPException, status
import redis.asyncio as redis
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    AsyncEngine,
    async_sessionmaker,
)

from app.src.conf.config import settings


SQLALCHEMY_DATABASE_URL = "${DATABASE}+${DRIVER_SYNC}://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}"
engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

engine: AsyncEngine = create_async_engine(
    settings.sqlalchemy_database_url_async,
    echo=False,
)

AsyncDBSession = async_sessionmaker(
    engine, autoflush=False, expire_on_commit=False, class_=AsyncSession
)


async def get_session():
    session = AsyncDBSession()
    try:
        yield session
    except SQLAlchemyError as error_message:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Database error: {str(error_message)}",
        )
    finally:
        await session.close()


redis_db0 = redis.from_url(
    settings.redis_url,
    db=0,
    encoding="utf-8",
    decode_responses=True,
)
pool_redis_db = redis.ConnectionPool.from_url(settings.redis_url)


async def get_redis_db1():
    client = redis.Redis(
        connection_pool=pool_redis_db,
        db=1,
        encoding="utf-8",
        decode_responses=False,
    )
    try:
        yield client
    except redis.RedisError as error_message:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Redis error: {str(error_message)}",
        )
    finally:
        await client.close()