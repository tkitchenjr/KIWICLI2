from pydantic import BaseModel, Field

# Error Response Schema
class ErrorResponse(BaseModel):
    error: str = Field(description="Error message describing the issue")
    detail: str = Field(default="", description="Optional detailed information about the error")
