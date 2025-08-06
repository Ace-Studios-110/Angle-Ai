from pydantic import BaseModel, Field
from typing import Optional

class CreateSessionSchema(BaseModel):
    title: Optional[str] = Field(default="Untitled", max_length=120)

class ChatRequestSchema(BaseModel):
    content: str = Field(...)

    # Optional: Add this if you want to prevent null explicitly (helps with OpenAPI docs or frontend errors)
    @classmethod
    def __get_validators__(cls):
        yield cls.validate_not_null

    @staticmethod
    def validate_not_null(value):
        if value is None:
            raise ValueError("content cannot be null")
        return value