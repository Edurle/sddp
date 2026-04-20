import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.database import init_db
from app.exceptions import BusinessError

logger = logging.getLogger(__name__)

app = FastAPI(title="SDD Backend", version="0.1.0")


@app.on_event("startup")
async def on_startup():
    await init_db()
    logger.info("Database initialized")


@app.exception_handler(BusinessError)
async def business_error_handler(request: Request, exc: BusinessError):
    return JSONResponse(
        status_code=400,
        content={"code": exc.code, "message": exc.message, "data": None},
    )


from app.api.router import router as api_router  # noqa: E402

app.include_router(api_router, prefix="/api/v1")
