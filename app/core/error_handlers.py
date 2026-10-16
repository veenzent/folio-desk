import logging
import uuid

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import CustomHTTPException


def register_error_handlers(app):
    logger = logging.getLogger("carbnb.error_handlers")

    @app.exception_handler(CustomHTTPException)
    async def custom_http_exception_handler(request: Request, exc: CustomHTTPException):
        # CustomHTTPException.detail is already a structured dict
        return JSONResponse(status_code=exc.status_code, content=exc.detail)

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        # If detail is already structured, return it as top-level; otherwise wrap
        detail = exc.detail
        if isinstance(detail, dict):
            return JSONResponse(status_code=exc.status_code, content=detail)
        return JSONResponse(status_code=exc.status_code, content={"error": detail})

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ):
        return JSONResponse(
            status_code=422,
            content={"error": "Validation error", "details": exc.errors()},
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        # Log full exception with a correlated id for easier debugging in logs
        error_id = uuid.uuid4().hex
        logger.exception("Unhandled exception (id=%s): %s", error_id, exc)
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error", "error_id": error_id},
        )
