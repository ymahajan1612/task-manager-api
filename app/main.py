from fastapi import FastAPI
from app.routes import tasks, auth
import logging

app = FastAPI()

logger = logging.getLogger("uvicorn")
logger.setLevel(logging.INFO)


@app.get("/")
def root():
    logger.info("Root endpoint called")
    return {"message": "Hello World"}


@app.get("/health", status_code=200)
def health_check() -> dict[str, str]:
    logger.info("Fetching health status")
    return {"status": "ok"}


app.include_router(tasks.router)
app.include_router(auth.router)