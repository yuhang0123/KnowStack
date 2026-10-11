from pydantic import BaseModel, Field
from enum import Enum

class ErrorCode(str, Enum):
    VALIDATION_ERROR = "Validation Error"
    NOT_FOUND = "Not Found"
    INTERNAL_ERROR = "internal_error"

class ErrorDetail(BaseModel):
    field: str = Field(description="Name of the field that failed validation")
    message: str = Field(description="Why the field is invalid")

class ErrorResponse(BaseModel):
    error_code: ErrorCode = Field(description="Machine-readable code for the frontend")
    error_message: str = Field(description="Short human-readable summary")
    error_details: list[ErrorDetail] | None = Field(default=None, description="Per-field errors, if any")