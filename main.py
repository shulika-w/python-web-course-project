"""
Main module
"""

from contextlib import asynccontextmanager
import pathlib
import sys
from time import time

from fastapi import FastAPI, Depends, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
import uvicorn

from app.src.conf.config import settings
from app.src.database.connect_db import engine, get_session, redis_db0, pool_redis_db
from app.src.routes import auth, users, tags, comments, images, rates


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles lifespan events.

    """
    healthy_start = await startup()
    if healthy_start:
        yield
        await shutdown()
    else:
        await engine.dispose()
        sys.exit()


app = FastAPI(lifespan=lifespan)


async def startup():
    """
    Handles startup events.

    """
    try:
        await redis_db0.ping()
    except Exception:
        return False
    await pool_redis_db.disconnect()
    await redis_db0.flushall()
    await FastAPILimiter.init(redis_db0)
    return True


async def shutdown():
    """
    Handles shutdown events.

    """
    await pool_redis_db.disconnect()
    await redis_db0.flushall()
    await engine.dispose()


origins = [f"{settings.api_protocol}://{settings.api_host}:{settings.api_port}"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next: callable):
    """
    Calculates a request's processing time.

    :param request: The request object.
    :type request: Request
    :param call_next: The next request's handler.
    :type call_next: callable
    :return: The response.
    :rtype: starlette.middleware.base._StreamingResponse
    """
    start_time = time()
    response = await call_next(request)
    process_time = time() - start_time
    response.headers["API-Process-Time"] = str(process_time)
    return response


BASE_API_ROUTE = "/api"

app.include_router(
    auth.router,
    prefix=BASE_API_ROUTE,
    dependencies=[
        Depends(
            RateLimiter(
                times=settings.rate_limiter_times,
                seconds=settings.rate_limiter_seconds,
            )
        )
    ],
)
app.include_router(
    users.router,
    prefix=BASE_API_ROUTE,
    dependencies=[
        Depends(
            RateLimiter(
                times=settings.rate_limiter_times,
                seconds=settings.rate_limiter_seconds,
            )
        )
    ],
)
app.include_router(
    images.router,
    prefix=BASE_API_ROUTE,
    dependencies=[
        Depends(
            RateLimiter(
                times=settings.rate_limiter_times,
                seconds=settings.rate_limiter_seconds,
            )
        )
    ],
)
app.include_router(
    comments.router,
    prefix=BASE_API_ROUTE,
    dependencies=[
        Depends(
            RateLimiter(
                times=settings.rate_limiter_times,
                seconds=settings.rate_limiter_seconds,
            )
        )
    ],
)
app.include_router(
    tags.router,
    prefix=BASE_API_ROUTE,
    dependencies=[
        Depends(
            RateLimiter(
                times=settings.rate_limiter_times,
                seconds=settings.rate_limiter_seconds,
            )
        )
    ],
)
app.include_router(
    rates.router,
    prefix=BASE_API_ROUTE,
    dependencies=[
        Depends(
            RateLimiter(
                times=settings.rate_limiter_times,
                seconds=settings.rate_limiter_seconds,
            )
        )
    ],
)


@app.get(
    BASE_API_ROUTE + "/healthchecker",
    dependencies=[
        Depends(
            RateLimiter(
                times=settings.rate_limiter_times,
                seconds=settings.rate_limiter_seconds,
            )
        )
    ],
)
async def healthchecker(session: AsyncSession = Depends(get_session)):
    """
    Handles a GET-operation to '/api/healthchecker' route and checks connecting to the database.

    :param session: The database session.
    :type session: AsyncSession
    :return: The message.
    :rtype: str
    """
    try:
        stmt = select(text("0"))
        result = await session.execute(stmt)
        result = result.scalar()
        if result is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database is not configured correctly",
            )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error connecting to the database",
        )
    return {"message": "OK"}


BASE_DIR = pathlib.Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"


class StaticFilesCache(StaticFiles):
    def __init__(
            self,
            *args,
            cachecontrol="public, max-age=31536000, s-maxage=31536000, immutable",
            **kwargs,
    ):
        self.cachecontrol = cachecontrol
        super().__init__(*args, **kwargs)

    def file_response(self, *args, **kwargs) -> Response:
        resp: Response = super().file_response(*args, **kwargs)
        resp.headers.setdefault("Cache-Control", self.cachecontrol)
        return resp


app.mount(
    "/static",
    app=StaticFilesCache(directory=STATIC_DIR, cachecontrol="private, max-age=3600"),
    name="static",
)


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    """
    Handles a GET-operation to get favicon.ico.

    :return: The favicon.ico.
    :rtype: FileResponse
    """
    return FileResponse(STATIC_DIR / "images/favicon.ico")


@app.get(
    "/",
    dependencies=[
        Depends(
            RateLimiter(
                times=settings.rate_limiter_times,
                seconds=settings.rate_limiter_seconds,
            )
        )
    ],
)
async def read_root():
    """
    Handles a GET-operation to root route and returns the message.

    :return: The message.
    :rtype: str
    """
    return {"message": settings.api_name}


if __name__ == "__main__":
    uvicorn.run("main:app", host=settings.api_host, port=settings.api_port)
