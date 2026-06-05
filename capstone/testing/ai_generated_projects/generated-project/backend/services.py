from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime
from models import TodoDBModel
from schemas import TodoCreateRequest

class TodoService:
    def __init__(self, db: Session):
        self.db = db

    def create_todo(self, request: TodoCreateRequest) -> TodoDBModel:
        todo = TodoDBModel(
            title=request.title,
            description=request.description,
        )
        self.db.add(todo)
        self.db.commit()
        self.db.refresh(todo)
        return todo

    def list_todos(self):
        return self.db.query(TodoDBModel).order_by(TodoDBModel.created_at.asc()).all()

    def delete_todo(self, todo_id: UUID) -> bool:
        todo = self.db.query(TodoDBModel).filter_by(id=todo_id).first()
        if not todo:
            return False
        self.db.delete(todo)
        self.db.commit()
        return True