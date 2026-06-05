from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime

class TodoCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)

class TodoResponse(BaseModel):
    id: UUID
    title: str
    description: str
    createdAt: datetime = Field(..., alias="created_at")

    class Config:
        orm_mode = True
        allow_population_by_field_name = True

class ErrorResponse(BaseModel):
    error: str