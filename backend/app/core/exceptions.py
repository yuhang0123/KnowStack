from fastapi import Request, FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from .errors import ErrorResponse, ErrorDetail, ErrorCode

import structlog
from structlog.contextvars import get_contextvars
logger = structlog.getLogger()

# --- CUSTOM EXCEPTION --- 

class AppError(Exception):
    status_code: int = 500
    error_code: ErrorCode = ErrorCode.INTERNAL_ERROR
    message: str = "500 Internal Error"

    def __init__(self, message: str | None = None):
        if (message is not None):
            self.message = message
        super().__init__(self.message)

# --- HANDLERS --- 

def _error_response(status_code: int, body: ErrorResponse) -> JSONResponse:
    body.request_id = get_contextvars().get("request_id")
    return JSONResponse(status_code=status_code, content=body.model_dump(mode="json"))

async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return _error_response(
        status_code=exc.status_code,
        body=ErrorResponse(
            error_code=exc.error_code,
            error_message=exc.message
        )
    )

"""
exc.errors()
1. type: why it failed (e.g. missing)
2. loc: where it failed (e.g. ("body", "<field name>"))
3. msg: pydantic message
4. input: value the client sent
"""
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    details = []
    for err in exc.errors():
        loc = err["loc"]
        field = get_error_field(loc)
        details.append(ErrorDetail(field=field, message=err["msg"]))

    logger.error(f"Request validation error on {request.method} {request.url.path}")
    return _error_response(
        422,
        ErrorResponse(
            error_code=ErrorCode.VALIDATION_ERROR,
            error_message="Invalid request. Please check the fields below.",
            error_details=details,
        ),
    )

# for internal diagnose only
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    # Log the real error server-side, but never expose it to the client
    logger.error("Unhandled error on %s %s", request.method, request.url.path)
    return _error_response(
        500,
        ErrorResponse(
            error_code=ErrorCode.INTERNAL_ERROR,
            error_message="An unexpected error occurred.",
        ),
    )


# --- REGISTRATION ---
def register_exception_handlers(app: FastAPI):
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)


# --- HELPER METHOD ---
def get_error_field(loc: tuple):
    field = ".".join(str(part) for part in loc[1:]) if len(loc) > 1 else str(loc[0])
    return field