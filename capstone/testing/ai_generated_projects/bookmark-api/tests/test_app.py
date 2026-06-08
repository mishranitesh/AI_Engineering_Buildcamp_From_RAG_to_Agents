import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from main import app
from db import Base, get_db
from services import BookmarkService
from data_models import BookmarkDB
import uuid

from business_models import Bookmark

# --- Setup in-memory test db and test session for all tests ---

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

# --- Unit Tests for BookmarkService ---

@pytest.fixture
def db_session():
    session = TestingSessionLocal()
    yield session
    session.rollback()
    session.close()

def test_create_bookmark_service(db_session):
    svc = BookmarkService()
    b = svc.create_bookmark(db_session, "Google", "https://google.com")
    assert isinstance(b, Bookmark)
    assert b.title == "Google"
    assert b.url == "https://google.com"
    assert b.id
    assert b.created_at

def test_list_bookmarks_service(db_session):
    svc = BookmarkService()
    # empty first
    bookmarks = svc.list_bookmarks(db_session)
    assert bookmarks == []

    # then add
    b = svc.create_bookmark(db_session, "Google", "https://google.com")
    bookmarks = svc.list_bookmarks(db_session)
    assert len(bookmarks) == 1
    assert bookmarks[0].id == b.id

def test_delete_existing_bookmark_service(db_session):
    svc = BookmarkService()
    b = svc.create_bookmark(db_session, "Google", "https://google.com")
    found = svc.delete_bookmark(db_session, b.id)
    assert found is True
    # Now should be gone
    after = svc.list_bookmarks(db_session)
    assert all(bb.id != b.id for bb in after)

def test_delete_non_existing_bookmark_service(db_session):
    svc = BookmarkService()
    non_existing_id = uuid.uuid4()
    found = svc.delete_bookmark(db_session, non_existing_id)
    assert found is False

# --- API Tests ---

def test_post_bookmark_success():
    payload = {
        "title": "FastAPI",
        "url": "https://fastapi.tiangolo.com/"
    }
    response = client.post("/bookmarks", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == payload["title"]
    assert data["url"] == payload["url"]
    assert "id" in data
    assert "created_at" in data

def test_post_bookmark_invalid_url():
    payload = {
        "title": "Bad URL",
        "url": "not-a-url"
    }
    response = client.post("/bookmarks", json=payload)
    assert response.status_code == 422 # validation error

def test_post_bookmark_missing_title():
    payload = {
        "url": "https://fastapi.tiangolo.com/"
    }
    response = client.post("/bookmarks", json=payload)
    assert response.status_code == 422

def test_post_bookmark_long_title():
    payload = {
        "title": "A"*300,  # Exceeds max_length=255
        "url": "https://fastapi.tiangolo.com/"
    }
    response = client.post("/bookmarks", json=payload)
    assert response.status_code == 422

def test_get_bookmarks_empty():
    response = client.get("/bookmarks")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert response.json() == []

def test_get_bookmarks_non_empty():
    # Add a bookmark first
    payload = {
        "title": "FastAPI",
        "url": "https://fastapi.tiangolo.com/"
    }
    post_resp = client.post("/bookmarks", json=payload)
    assert post_resp.status_code == 201
    response = client.get("/bookmarks")
    assert response.status_code == 200
    bookmarks = response.json()
    assert len(bookmarks) >= 1
    assert any(b["title"] == "FastAPI" for b in bookmarks)

def test_delete_bookmark_success():
    # Add then delete
    payload = {
        "title": "FastAPI",
        "url": "https://fastapi.tiangolo.com/"
    }
    post_resp = client.post("/bookmarks", json=payload)
    bid = post_resp.json()["id"]
    del_resp = client.delete(f"/bookmarks/{bid}")
    assert del_resp.status_code == 204
    # Check that it's removed
    get_resp = client.get("/bookmarks")
    bookmarks = get_resp.json()
    assert all(b["id"] != bid for b in bookmarks)

def test_delete_bookmark_not_found():
    random_id = str(uuid.uuid4())
    del_resp = client.delete(f"/bookmarks/{random_id}")
    assert del_resp.status_code == 404
    assert del_resp.json()["detail"] == "Bookmark not found"

def test_delete_bookmark_invalid_uuid():
    invalid_uuid = "not-a-uuid"
    del_resp = client.delete(f"/bookmarks/{invalid_uuid}")
    # FastAPI will catch as 422 unprocessable
    assert del_resp.status_code == 422

# --- Edge Cases ---

@pytest.mark.parametrize(
    "title,url",
    [
        ("", "https://valid.url/"),                  # Empty title allowed but might fail schema
        ("EdgeTitle", ""),                           # Empty url not allowed
        ("Unicode测试书签", "https://测试.公司/"),   # Unicode title and url
        ("T" * 255, "https://fastapi.tiangolo.com/"),# Max allowed title length
    ]
)
def test_post_bookmark_edge_cases(title, url):
    payload = {
        "title": title,
        "url": url
    }
    response = client.post("/bookmarks", json=payload)
    if not title or not url:
        # Both title (required string) and url (required and must be valid AnyUrl) must be present
        assert response.status_code == 422
    else:
        # Valid case for unicode/long
        assert response.status_code == 201
        assert response.json()["title"] == title
        assert response.json()["url"] == url