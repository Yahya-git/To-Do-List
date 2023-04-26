import os

import sqltap
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from src.logger import setup_logger

from .controller import auth, reports, tasks, users
from .handler import scheduler

logger = setup_logger()

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def set_body(request: Request, body: bytes):
    async def receive():
        return {"type": "http.request", "body": body}

    request._receive = receive


async def get_body(request: Request) -> bytes:
    body = await request.body()
    await set_body(request, body)
    return body


@app.middleware("http")
async def app_entry(request: Request, call_next):
    logger.info(f"Incoming Request: {request.method} {request.url}")
    await set_body(request, await request.body())
    logger.info(f"Request Body: {await get_body(request)}")
    response = await call_next(request)
    logger.info(f"Outgoing Response: {response.status_code}")
    res_body = b""
    async for chunk in response.body_iterator:
        res_body += chunk
    logger.info(f"Response Body: {res_body}")
    return Response(
        content=res_body,
        status_code=response.status_code,
        headers=dict(response.headers),
        media_type=response.media_type,
    )


@app.middleware("http")
async def add_sql_tap(request: Request, call_next):
    profiler = sqltap.start()
    response = await call_next(request)
    statistics = profiler.collect()
    sqltap.report(statistics, "report.txt", report_format="text")
    return response


app.include_router(users.router)
app.include_router(tasks.router)
app.include_router(auth.router)
app.include_router(scheduler.router)
app.include_router(reports.router)


@app.get("/")
async def root():
    return {"message": "Testing"}
