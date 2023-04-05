import logging
import os
from logging.handlers import RotatingFileHandler

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from app import scheduler

from .routers import auth, tasks, users

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
file_handler = RotatingFileHandler("app.log", maxBytes=10000000, backupCount=5)
file_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# @app.middleware("http")
# async def log_request(request: Request, call_next):
#     logger.info(f'{request.method} {request.url}')
#     req_body = b""
#     async for chunk in request.stream():
#         req_body += chunk
#     logger.info(f'Request body: {req_body}')
#     response = await call_next(request)
#     logger.info(f'Status code: {response.status_code}')
#     res_body = b""
#     async for chunk in response.body_iterator:
#         res_body += chunk
#     logger.info(f'Response body: {res_body}')
#     return Response(
#         content=res_body,
#         status_code=response.status_code,
#         headers=dict(response.headers),
#         media_type=response.media_type
#     )


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
    logger.info(f"Outgoing Response: {response.status_code} {response.headers}")
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


app.include_router(users.router)
app.include_router(tasks.router)
app.include_router(auth.router)
app.include_router(scheduler.router)


@app.get("/")
async def root():
    return {"message": "Testing"}
