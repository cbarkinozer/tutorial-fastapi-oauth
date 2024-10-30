from math import ceil
import redis.asyncio as redis
import uvicorn
from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi import status
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter

# pip install fastapi-limiter
# docker run --name my-redis-server -p 6379:6379 -d redis redis-server  --loglevel warning


REDIS_URL = "redis://127.0.0.1:6379"


async def service_name_identifier(request: Request):
    service = request.headers.get("Service-Name")
    return service


async def custom_callback(request: Request, response: Response, pexpire: int):
    """
    default callback when too many requests
    :param request:
    :param pexpire: The remaining milliseconds
    :param response:
    :return:
    """
    expire = ceil(pexpire / 1000)

    raise HTTPException(
        status.HTTP_429_TOO_MANY_REQUESTS,
        f"Too Many Requests. Retry after {expire} seconds.",
        headers={"Retry-After": str(expire)},
    )


@asynccontextmanager
async def lifespan(_: FastAPI):
    redis_connection = redis.from_url(REDIS_URL, encoding="utf8")
    await FastAPILimiter.init(
        redis=redis_connection,
        identifier=service_name_identifier,
        http_callback=custom_callback,
    )
    yield
    await FastAPILimiter.close()


app = FastAPI(lifespan=lifespan)


@app.get("/")
async def index():
    return {"msg": "This endpoint has no limits."}


@app.get("/search", dependencies=[Depends(RateLimiter(times=2, seconds=5))])
async def search_handler(request: Request):
    return {"msg": "This endpoint has a rate limit of 2 requests per 5 seconds."}


@app.get("/upload", dependencies=[Depends(RateLimiter(times=2, seconds=10))])
async def upload_handler(request: Request):
    return {"msg": "This endpoint has a rate limit of 2 requests per 10 seconds."}


if __name__ == "__main__":
    uvicorn.run(app, port=7000)