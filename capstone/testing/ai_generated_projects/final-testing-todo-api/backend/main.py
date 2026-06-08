from fastapi import FastAPI, HTTPException, status, Depends
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import uuid4
from sqlalchemy import (
    Column,
    String,
    DateTime,
    create_engine,
    text
)
from sqlalchemy.orm import (
    declarative_base,
    sessionmaker,
    Session
)

# --- Data Model (DB Schema) ---
Base = declarative_base()


class TodoDBModel(Base):
    __tablename__ = "todos"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    title = Column(String(255), nullable=False)
    description = Column(String(1024), nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=text("(datetime('now'))"))


# --- Business Model (Domain Logic) ---
class Todo:
    def __init__(self, id: str, title: str, description: str, created_at: datetime):
        self.id = id
        self.title = title
        self.description = description
        self.created_at = created_at


# --- API Schemas (Request/Response) ---
class TodoCreateRequest(BaseModel):
    title: str = Field(..., max_length=255)
    description: Optional[str] = Field(default=None, max_length=1024)


class TodoResponse(BaseModel):
    id: str
    title: str
    description: Optional[str]
    createdAt: datetime

    @classmethod
    def from_domain(cls, todo: Todo):
        return cls(
            id=todo.id,
            title=todo.title,
            description=todo.description,
            createdAt=todo.created_at,
        )


class ErrorResponse(BaseModel):
    detail: str


# --- Database Dependency ---
DATABASE_URL = "sqlite:///./todo.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- Service Layer (Business Logic) ---
class TodoService:
    @staticmethod
    def create_todo(db: Session, title: str, description: Optional[str]) -> Todo:
        todo_db = TodoDBModel(
            id=str(uuid4()),
            title=title,
            description=description,
            created_at=datetime.utcnow()
        )
        db.add(todo_db)
        db.commit()
        db.refresh(todo_db)
        return Todo(
            id=todo_db.id,
            title=todo_db.title,
            description=todo_db.description,
            created_at=todo_db.created_at
        )

    @staticmethod
    def list_todos(db: Session) -> List[Todo]:
        todos_db = db.query(TodoDBModel).order_by(TodoDBModel.created_at.desc()).all()
        return [
            Todo(
                id=row.id,
                title=row.title,
                description=row.description,
                created_at=row.created_at
            )
            for row in todos_db
        ]

    @staticmethod
    def delete_todo(db: Session, todo_id: str) -> None:
        todo_db = db.query(TodoDBModel).filter(TodoDBModel.id == todo_id).first()
        if not todo_db:
            raise ValueError("Todo not found")
        db.delete(todo_db)
        db.commit()


# --- App & Routes (API Boundaries) ---
app = FastAPI(title="Todo API")


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


@app.post(
    "/todos",
    response_model=TodoResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Todos"]
)
def create_todo(
    req: TodoCreateRequest,
    db: Session = Depends(get_db)
):
    todo = TodoService.create_todo(db, req.title, req.description)
    return TodoResponse.from_domain(todo)


@app.get(
    "/todos",
    response_model=List[TodoResponse],
    status_code=status.HTTP_200_OK,
    tags=["Todos"]
)
def list_todos(
    db: Session = Depends(get_db)
):
    todos = TodoService.list_todos(db)
    return [TodoResponse.from_domain(todo) for todo in todos]


@app.delete(
    "/todos/{todo_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        404: {"model": ErrorResponse}
    },
    tags=["Todos"]
)
def delete_todo(
    todo_id: str,
    db: Session = Depends(get_db)
):
    try:
        TodoService.delete_todo(db, todo_id)
        return
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )