from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.sqlite import BLOB as UUID
from datetime import datetime
import uuid

from db import Base


class BookmarkDB(Base):
    __tablename__ = "bookmarks"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, nullable=False)
    url = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)