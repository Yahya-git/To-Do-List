import os

from fastapi import FastAPI

from .routers import auth, users

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

app = FastAPI()

app.include_router(users.router)
app.include_router(auth.router)


@app.get("/")
async def root():
    return {"message": "Testing"}
