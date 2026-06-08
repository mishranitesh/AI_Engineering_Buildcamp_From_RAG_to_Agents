import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, clear_mappers

from main import (
    app, Base, get_db, TodoService, TodoDBModel, TodoCreateRequest, Todo
)

from uuid import uuid4
from datetime import datetime

# --------- Test Setup ---------

# Use an in-memory SQLite for tests
TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(bind=engine)

# Override the dependency to use test db
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="function")
def db_session():
    # Setup (fresh db each function)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

# --------- UNIT TESTS: Service Layer ---------

def test_create_todo_service(db_session):
    title = "Test TODO"
    description = "Testing create"
    todo = TodoService.create_todo(db_session, title, description)
    assert isinstance(todo, Todo)
    assert todo.title == title
    assert todo.description == description
    assert todo.id is not None
    # Check that in DB
    found = db_session.query(TodoDBModel).filter_by(id=todo.id).first()
    assert found is not None
    assert found.title == title

def test_list_todos_service_empty(db_session):
    todos = TodoService.list_todos(db_session)
    assert todos == []

def test_list_todos_service_order(db_session):
    # Insert multiple todos
    t1 = TodoService.create_todo(db_session, "First", "desc1")
    t2 = TodoService.create_todo(db_session, "Second", "desc2")
    todos = TodoService.list_todos(db_session)
    # Most recent first (by created_at descending)
    assert todos[0].id == t2.id
    assert todos[1].id == t1.id

def test_delete_todo_service_success(db_session):
    # Add todo
    todo = TodoService.create_todo(db_session, "DelMe", "desc")
    TodoService.delete_todo(db_session, todo.id)
    assert db_session.query(TodoDBModel).filter_by(id=todo.id).first() is None

def test_delete_todo_service_not_found(db_session):
    with pytest.raises(ValueError) as exc:
        TodoService.delete_todo(db_session, "non-existing-id")
    assert "Todo not found" in str(exc.value)

# Edge: deleting twice
def test_delete_todo_service_twice(db_session):
    todo = TodoService.create_todo(db_session, "Twice", None)
    TodoService.delete_todo(db_session, todo.id)
    with pytest.raises(ValueError):
        TodoService.delete_todo(db_session, todo.id)

# --------- API TESTS ---------

def test_create_todo_api(client):
    resp = client.post("/todos", json={"title": "ApiTodo", "description": "desc"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "ApiTodo"
    assert data["description"] == "desc"
    assert isinstance(data["id"], str)
    assert "createdAt" in data

def test_create_todo_api_no_description(client):
    resp = client.post("/todos", json={"title": "NoDesc"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["description"] is None

def test_create_todo_api_title_too_long(client):
    too_long_title = "a" * 256
    resp = client.post("/todos", json={"title": too_long_title, "description": "desc"})
    assert resp.status_code == 422

def test_create_todo_api_description_too_long(client):
    too_long_desc = "x" * 1025
    resp = client.post("/todos", json={"title": "ok", "description": too_long_desc})
    assert resp.status_code == 422

def test_list_todos_api_empty(client):
    resp = client.get("/todos")
    assert resp.status_code == 200
    assert resp.json() == []

def test_list_todos_api_with_entries(client):
    # Create two todos
    r1 = client.post("/todos", json={"title": "T1"})
    r2 = client.post("/todos", json={"title": "T2"})
    resp = client.get("/todos")
    assert resp.status_code == 200
    data = resp.json()
    titles = [todo['title'] for todo in data]
    # Most recent first
    assert titles[0] == "T2"
    assert titles[1] == "T1"

def test_delete_todo_api_success(client):
    # Add
    r = client.post("/todos", json={"title": "DeleteMe"})
    todo_id = r.json()["id"]
    resp = client.delete(f"/todos/{todo_id}")
    assert resp.status_code == 204
    # Should be gone
    resp2 = client.get("/todos")
    assert all(todo["id"] != todo_id for todo in resp2.json())

def test_delete_todo_api_not_found(client):
    resp = client.delete(f"/todos/{uuid4()}")
    assert resp.status_code == 404
    data = resp.json()
    assert "error" in data["detail"]
    assert data["detail"]["error"] == "Todo not found"

def test_delete_todo_api_invalid_id_format(client):
    bad_id = "not-a-uuid"
    resp = client.delete(f"/todos/{bad_id}")
    # Still returns 404, as per logic, since no such row
    assert resp.status_code == 404

# --------- EDGE CASES ---------

def test_create_todo_empty_title(client):
    # Even "" passes Pydantic, only max_length enforced
    resp = client.post("/todos", json={"title": "", "description": "desc"})
    assert resp.status_code == 201  # Accepts empty

def test_create_todo_null_title(client):
    resp = client.post("/todos", json={"description": "desc"})
    assert resp.status_code == 422  # Required

def test_delete_todo_already_deleted(client):
    # Create and delete
    r = client.post("/todos", json={"title": "ToBeDeleted"})
    todo_id = r.json()["id"]
    del1 = client.delete(f"/todos/{todo_id}")
    assert del1.status_code == 204
    del2 = client.delete(f"/todos/{todo_id}")
    assert del2.status_code == 404

def test_created_at_field_format(client):
    r = client.post("/todos", json={"title": "DatetimeTest"})
    assert r.status_code == 201
    dtstr = r.json()["createdAt"]
    # try parsing
    from dateutil import parser
    dt = parser.isoparse(dtstr)
    assert isinstance(dt, datetime)