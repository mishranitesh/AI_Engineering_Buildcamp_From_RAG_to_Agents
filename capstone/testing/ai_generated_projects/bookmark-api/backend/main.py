from fastapi import FastAPI, HTTPException, Depends, status
from typing import List
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy.orm import Session, declarative_base, sessionmaker
from sqlalchemy import create_engine

from db import get_db, engine, Base
from api_schemas import (
    BookmarkCreateRequest,
    BookmarkResponse,
)
from services import BookmarkService

app = FastAPI()

Base.metadata.create_all(bind=engine)

bookmark_service = BookmarkService()


@app.post(
    "/bookmarks",
    response_model=BookmarkResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_bookmark(
    bookmark_req: BookmarkCreateRequest, db: Session = Depends(get_db)
):
    bookmark = bookmark_service.create_bookmark(
        db, bookmark_req.title, bookmark_req.url
    )
    return BookmarkResponse.from_business(bookmark)


@app.get(
    "/bookmarks",
    response_model=List[BookmarkResponse],
)
def list_bookmarks(db: Session = Depends(get_db)):
    bookmarks = bookmark_service.list_bookmarks(db)
    return [BookmarkResponse.from_business(b) for b in bookmarks]


@app.delete(
    "/bookmarks/{bookmark_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_bookmark(bookmark_id: UUID, db: Session = Depends(get_db)):
    deleted = bookmark_service.delete_bookmark(db, bookmark_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Bookmark not found")
    return None