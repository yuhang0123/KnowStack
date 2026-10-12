import structlog
from structlog import configure
from structlog.contextvars import (
    merge_contextvars,
    clear_contextvars,
    bind_contextvars
)
import logging
from logging.handlers import RotatingFileHandler
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from pathlib import Path

# better not to use BaseHTTPMiddleware as quirks exist
# best for generating or extracting Request IDs from HTTP header
from asgi_correlation_id import CorrelationIdMiddleware
import re
import uuid

logger = structlog.get_logger()
REQUEST_ID_HEADER = "X-Request-ID"
_VALID_ID = re.compile(r"^[A-Za-z0-9_-]{1,64}$")

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        clear_contextvars()

        # extract request id from header
        # generate a new one if not found
        header = request.headers.get(REQUEST_ID_HEADER)
        request_id = header if header and _VALID_ID.match(header) else str(uuid.uuid4())

        bind_contextvars(request_id=request_id)

        # retrieve request detail
        client_ip = request.client.host
        method = request.method
        url = request.url.path

        try:
            # process the request
            response = await call_next(request)
        except Exception:
            logger.warning(f"Request Failed: {method} {url} from {client_ip}")
            raise

        logger.info(f"Request Success: {method} {url} from {client_ip}")

        response.headers[REQUEST_ID_HEADER] = request_id
        return response

        


def setup_logging(log_level, log_json, log_file):
    """
    1. Build processor list
        - one for merges in context variables
        - one for adding log level
        - one for adding a timestamp
        - one for rendering exception traceback when log an error with exc_info

    2. Choose renderer (i.e. last processor in the chain)
        - if log_json is TRUE -> JSON renderer
        - if log_json is FALSE -> console renderer

    3. Call structlog's configure function with:
        - processors = shared processors + renderer
        - wrapper class that filter log_level (via make_filtering_bound_logger function)
        - cache_logger_on_first_use = TRUE
    """
    # work for plain string and Enum
    level_name = getattr(log_level, "value", log_level)
    level = getattr(logging, level_name)

    # choose renderer
    # if log_json:
    #     renderer = structlog.processors.JSONRenderer()
    # else:
    #     renderer = structlog.dev.ConsoleRenderer()

    shared_processors = [
        merge_contextvars,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_log_level
    ]

    # if log_json:
    #     processors.append(structlog.processors.format_exc_info)

    # processors.append(renderer)

    # FOR TERMINAL PRINT
    # configure(
    #     processors=processors,
    #     wrapper_class=structlog.make_filtering_bound_logger(getattr(logging, log_level)),
    #     cache_logger_on_first_use=True
    # )

    configure(
        processors=[
            structlog.stdlib.filter_by_level, # drop events below the configured level
             *shared_processors, # unpack the prep list
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter # package the event so that stdlib can pick it up and render it
        ],
        logger_factory=structlog.stdlib.LoggerFactory(), # create standard lib logger
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True
    )

    if log_file:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)

    file_formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors, # handle log lines that did not come from structlog
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer()
        ]
    )

    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setFormatter(file_formatter)

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(file_handler)
    root.setLevel(level)

    # uvicorn attach its own handler with its own format
    # propagate=True will make the message travel up to the rool logger
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        uvicorn_logger = logging.getLogger(name)
        uvicorn_logger.handlers.clear()
        uvicorn_logger.propagate = True 
    