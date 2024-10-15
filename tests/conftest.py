import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(f"{os.path.dirname(SCRIPT_DIR)}/app")

from datetime import date
from unittest.mock import MagicMock

from fastapi_limiter import FastAPILimiter
from httpx import AsyncClient
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    AsyncEngine,
    async_sessionmaker,
)

from main import app
from app.src.database.models import User
from app.src.conf.config import settings
from app.src.database.models import Base, User
from app.src.database.connect_db import get_session, redis_db0

SQLALCHEMY_DATABASE_URL_ASYNC = "sqlite+aiosqlite:///:memory:"

engine: AsyncEngine = create_async_engine(
    SQLALCHEMY_DATABASE_URL_ASYNC,
    echo=False,
)

AsyncDBSession = async_sessionmaker(
    engine, autoflush=False, expire_on_commit=False, class_=AsyncSession
)


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="session")
async def session():
    session = AsyncDBSession()
    try:
        yield session
    finally:
        await session.close()


@pytest.fixture(scope="module")
async def client(session):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async def override_get_session():
        try:
            yield session
        finally:
            await session.close()

    app.dependency_overrides[get_session] = override_get_session
    await FastAPILimiter.init(redis_db0)
    yield AsyncClient(
        app=app,
        base_url=f"{settings.api_protocol}://{settings.api_host}:{settings.api_port}",
    )


@pytest.fixture(scope="function")
async def token(client, user, session, monkeypatch):
    mock_add_task = MagicMock()
    monkeypatch.setattr("fastapi.BackgroundTasks.add_task", mock_add_task)
    await client.post(
        "/api/auth/signup",
        data={
            "username": user.get("username"),
            "email": user.get("email"),
            "password": user.get("password"),
        },
    )
    stmt = select(User).filter(User.email == user.get("email"))
    current_user = await session.execute(stmt)
    current_user = current_user.scalar()
    current_user.is_email_confirmed = True
    await session.commit()
    response = await client.post(
        "/api/auth/login",
        data={"username": user.get("email"), "password": user.get("password")},
    )
    data = response.json()
    return data["access_token"]


@pytest.fixture(scope="session")
def user():
    return {
        "username": "test",
        "email": "test@test.com",
        "password": "1234567890",
    }


@pytest.fixture(scope="session")
def user_to_update():
    return {
        "first_name": "test",
        "last_name": "test",
        "phone": "1234567890",
        "birthday": "2001-01-01",
    }


@pytest.fixture(scope="session")
def wrong_email():
    return "wrong@test.com"


@pytest.fixture(scope="session")
def new_password():
    return "0987654321"
