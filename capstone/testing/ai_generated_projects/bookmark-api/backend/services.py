from sqlalchemy.orm import Session
from uuid import uuid4, UUID
from datetime import datetime

from data_models import BookmarkDB
from business_models import Bookmark


class BookmarkService:
    def create_bookmark(self, db: Session, title: str, url: str) -> Bookmark:
        db_bookmark = BookmarkDB(
            id=str(uuid4()),
            title=title,
            url=url,
            created_at=datetime.utcnow(),
        )
        db.add(db_bookmark)
        db.commit()
        db.refresh(db_bookmark)
        return Bookmark(
            id=db_bookmark.id,
            title=db_bookmark.title,
            url=db_bookmark.url,
            created_at=db_bookmark.created_at,
        )

    def list_bookmarks(self, db: Session) -> list[Bookmark]:
        bookmarks = (
            db.query(BookmarkDB)
            .order_by(BookmarkDB.created_at.desc())
            .all()
        )
        return [
            Bookmark(
                id=b.id,
                title=b.title,
                url=b.url,
                created_at=b.created_at,
            )
            for b in bookmarks
        ]

    def delete_bookmark(self, db: Session, bookmark_id: UUID) -> bool:
        bm = db.query(BookmarkDB).filter_by(id=str(bookmark_id)).first()
        if bm is not None:
            db.delete(bm)
            db.commit()
            return True
        return False