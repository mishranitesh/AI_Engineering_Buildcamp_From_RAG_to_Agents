import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from uuid import uuid4, UUID
from datetime import datetime
import main
import models
import services
import schemas

# ----------- Fixtures and helpers ------------

@pytest.fixture
def client():
    app = main.app
    return TestClient(app)

@pytest.fixture
def mock_db_session():
    return MagicMock()

@pytest.fixture
def todo_obj():
    class Dummy:
        pass
    obj = Dummy()
    obj.id = uuid4()
    obj.title = "Walk the dog"
    obj.description = "Take Fido for a walk in the park."
    obj.created_at = datetime(2023, 12, 31, 12, 0, 0)
    return obj

@pytest.fixture
def todo_data(todo_obj):
    return {
        "id": str(todo_obj.id),
        "title": todo_obj.title,
        "description": todo_obj.description,
        "createdAt": todo_obj.created_at.isoformat(),
    }

# ----------- Unit Tests: Services ------------

def test_create_todo_service_success(mock_db_session):
    request = schemas.TodoCreateRequest(title="Test", description="Test desc")
    svc = services.TodoService(mock_db_session)
    # Patch DB methods
    mock_db_session.add = MagicMock()
    mock_db_session.commit = MagicMock()
    mock_db_session.refresh = lambda t: None

    todo_model_cls = models.TodoDBModel
    todo = svc.create_todo(request)
    assert isinstance(todo, todo_model_cls)
    assert todo.title == request.title
    assert todo.description == request.description

def test_list_todos_service_returns_ordered(mock_db_session, todo_obj):
    svc = services.TodoService(mock_db_session)
    mock_db_session.query().order_by().all.return_value = [todo_obj]
    todos = svc.list_todos()
    assert todos == [todo_obj]

def test_delete_todo_service_found_and_deleted(mock_db_session, todo_obj):
    svc = services.TodoService(mock_db_session)
    # Simulate found
    mock_q = MagicMock()
    mock_q.filter_by.return_value.first.return_value = todo_obj
    mock_db_session.query.return_value = mock_q
    mock_db_session.delete = MagicMock()
    mock_db_session.commit = MagicMock()
    
    result = svc.delete_todo(todo_obj.id)
    assert result is True

def test_delete_todo_service_not_found(mock_db_session, todo_obj):
    svc = services.TodoService(mock_db_session)
    # Simulate not found
    mock_q = MagicMock()
    mock_q.filter_by.return_value.first.return_value = None
    mock_db_session.query.return_value = mock_q
    
    result = svc.delete_todo(uuid4())
    assert result is False

# ----------- API Tests: Happy paths ------------

def test_create_todo_api(client):
    with patch("main.get_db", return_value=(v for v in [MagicMock()])):
        with patch.object(services.TodoService, "create_todo") as mock_create:
            todo_id = uuid4()
            now = datetime.utcnow()
            mock_create.return_value = MagicMock(
                id=todo_id, title="Test", description="Test desc", created_at=now
            )
            resp = client.post("/todos", json={"title": "Test", "description": "Test desc"})
            assert resp.status_code == 201
            data = resp.json()
            assert data["id"] == str(todo_id)
            assert data["title"] == "Test"
            assert data["description"] == "Test desc"
            assert "createdAt" in data

def test_list_todos_api(client):
    with patch("main.get_db", return_value=(v for v in [MagicMock()])):
        with patch.object(services.TodoService, "list_todos") as mock_list:
            todo_id = uuid4()
            now = datetime.utcnow()
            mock_list.return_value = [
                MagicMock(id=todo_id, title="Foo", description="Bar", created_at=now)
            ]
            resp = client.get("/todos")
            assert resp.status_code == 200
            data = resp.json()
            assert isinstance(data, list)
            assert len(data) == 1
            assert data[0]["id"] == str(todo_id)
            assert data[0]["title"] == "Foo"

def test_delete_todo_api_success(client):
    with patch("main.get_db", return_value=(v for v in [MagicMock()])):
        with patch.object(services.TodoService, "delete_todo") as mock_delete:
            mock_delete.return_value = True
            todo_id = str(uuid4())
            resp = client.delete(f"/todos/{todo_id}")
            assert resp.status_code == 204

def test_delete_todo_api_404(client):
    with patch("main.get_db", return_value=(v for v in [MagicMock()])):
        with patch.object(services.TodoService, "delete_todo") as mock_delete:
            mock_delete.return_value = False
            fake_id = str(uuid4())
            resp = client.delete(f"/todos/{fake_id}")
            assert resp.status_code == 404
            assert resp.json()["detail"] == "Todo item not found"

# ----------- API Tests: Edge cases ------------

@pytest.mark.parametrize("payload,missing_field", [
    ({"description": "hello"}, "title"),
    ({"title": "title"}, "description"),
    ({}, "required field"),
])
def test_create_todo_validation_missing_fields(client, payload, missing_field):
    resp = client.post("/todos", json=payload)
    assert resp.status_code == 422
    assert "detail" in resp.json()
    # Validate error about missing field
    detail = str(resp.json()["detail"])
    assert missing_field in detail

def test_create_todo_title_too_long(client):
    payload = {"title": "a" * 201, "description": "desc"}
    resp = client.post("/todos", json=payload)
    assert resp.status_code == 422

def test_create_todo_empty_description(client):
    payload = {"title": "walk dog", "description": ""}
    resp = client.post("/todos", json=payload)
    assert resp.status_code == 422

def test_delete_todo_invalid_uuid(client):
    resp = client.delete("/todos/not-a-uuid")
    assert resp.status_code == 422
    assert "detail" in resp.json()

def test_list_todos_empty(client):
    with patch("main.get_db", return_value=(v for v in [MagicMock()])):
        with patch.object(services.TodoService, "list_todos") as mock_list:
            mock_list.return_value = []
            resp = client.get("/todos")
            assert resp.status_code == 200
            assert resp.json() == []

# ----------- Edge case: create and delete sequence ------------

def test_create_and_delete_flow(client):
    todo_id = uuid4()
    created_at = datetime.utcnow()
    # Step 1: POST -> create
    with patch("main.get_db", return_value=(v for v in [MagicMock()])):
        with patch.object(services.TodoService, "create_todo") as mock_create:
            mock_create.return_value = MagicMock(
                id=todo_id, title="Z", description="Y", created_at=created_at
            )
            post_resp = client.post("/todos", json={"title": "Z", "description": "Y"})
            assert post_resp.status_code == 201
            assert post_resp.json()["id"] == str(todo_id)
    # Step 2: DELETE same
    with patch("main.get_db", return_value=(v for v in [MagicMock()])):
        with patch.object(services.TodoService, "delete_todo") as mock_delete:
            mock_delete.return_value = True
            del_resp = client.delete(f"/todos/{todo_id}")
            assert del_resp.status_code == 204

# ----------- Startup event test ------------

def test_startup_creates_tables(monkeypatch):
    called = {}
    class Dummy:
        def create_all(self, bind):
            called["ok"] = True
    monkeypatch.setattr(main, "Base", type("B", (), {"metadata": type("M", (), {"create_all": Dummy().create_all})()})())
    monkeypatch.setattr(main, "get_engine", lambda: "dbengine")
    # Should not raise
    main.on_startup()
    assert called.get("ok") is True