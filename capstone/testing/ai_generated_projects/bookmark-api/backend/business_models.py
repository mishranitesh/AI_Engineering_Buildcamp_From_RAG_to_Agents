from datetime import datetime
from uuid import UUID


class Bookmark:
    def __init__(
        self,
        id: str,
        title: str,
        url: str,
        created_at: datetime,
    ):
        self.id = UUID(id)
        self.title = title
        self.url = url
        self.created_at = created_at