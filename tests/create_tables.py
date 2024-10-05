import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(f"{os.path.dirname(SCRIPT_DIR)}/app")

import asyncio

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncEngine,
)

from app.src.conf.config import settings
from app.src.database.models import Base


engine: AsyncEngine = create_async_engine(
    settings.sqlalchemy_database_url_async,
    echo=False,
)


async def async_main(engine) -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(async_main(engine))