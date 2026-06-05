from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from models import Base, get_engine, get_db, TodoDBModel
from schemas import TodoCreateRequest, TodoResponse, ErrorResponse
from services import TodoService

app = FastAPI()

# Create DB tables on startup (for demo purposes only; in production, use alembic, etc)
@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=get_engine())

@app.post(
    "/todos",
    response_model=TodoResponse,
    status_code=status.HTTP_201_CREATED
)
def create_todo(
    todo_in: TodoCreateRequest,
    db: Session = Depends(get_db)
):
    todo = TodoService(db).create_todo(todo_in)
    return TodoResponse.from_orm(todo)

@app.get(
    "/todos",
    response_model=List[TodoResponse]
)
def list_todos(
    db: Session = Depends(get_db)
):
    todos = TodoService(db).list_todos()
    return [TodoResponse.from_orm(todo) for todo in todos]

@app.delete(
    "/todos/{todo_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={404: {"model": ErrorResponse}}
)
def delete_todo(
    todo_id: UUID,
    db: Session = Depends(get_db)
):
    deleted = TodoService(db).delete_todo(todo_id)
    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Todo item not found"
        )
    return JSONResponse(status_code=204, content=None)