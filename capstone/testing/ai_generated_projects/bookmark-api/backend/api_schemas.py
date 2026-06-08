from pydantic import BaseModel, AnyUrl, Field
from datetime import datetime
from typing import Optional
from uuid import UUID
from business_models import Bookmark


class BookmarkCreateRequest(BaseModel):
    title: str = Field(..., max_length=255)
    url: AnyUrl

    class Config:
        schema_extra = {
            "example": {
                "title": "FastAPI Docs",
                "url": "https://fastapi.tiangolo.com/",
            }
        }


class BookmarkResponse(BaseModel):
    id: UUID
    title: str
    url: str
    created_at: datetime

    @classmethod
    def from_business(cls, bookmark: "Bookmark"):
        return cls(
            id=bookmark.id,
            title=bookmark.title,
            url=bookmark.url,
            created_at=bookmark.created_at,
        )

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "id": "ae3e55e8-447f-4f28-816b-1b2a3d5f882f",
                "title": "FastAPI Docs",
                "url": "https://fastapi.tiangolo.com/",
                "created_at": "2024-06-12T10:23:54.123456",
            }
        }