import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from main import app
from models import Base, InventoryItem
from services import get_db
from auth import User

# Use an in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency override for get_db
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

# Dependency override for get_current_user
def get_admin_user():
    return User(username="admin", is_admin=True)

def get_regular_user():
    return User(username="user", is_admin=False)

client = TestClient(app)

@pytest.fixture(scope="session", autouse=True)
def create_test_db():
    # Create tables, shared for all tests in session
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()

@pytest.fixture
def admin_client(monkeypatch):
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides["get_current_user"] = get_admin_user
    yield client
    if "get_current_user" in app.dependency_overrides:
        del app.dependency_overrides["get_current_user"]

@pytest.fixture
def regular_client(monkeypatch):
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides["get_current_user"] = get_regular_user
    yield client
    if "get_current_user" in app.dependency_overrides:
        del app.dependency_overrides["get_current_user"]

def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}

# ---- UNIT TESTS ----

def test_create_inventory_item_success(db_session):
    from services import create_inventory_item
    from schemas import InventoryItemCreate

    item = InventoryItemCreate(name="Widget", quantity=10, price=5.0)
    db_obj = create_inventory_item(db_session, item)
    assert db_obj.name == "Widget"
    assert db_obj.quantity == 10
    assert db_obj.price == 5.0
    assert db_obj.id is not None

def test_create_inventory_item_duplicate(db_session):
    from services import create_inventory_item
    from schemas import InventoryItemCreate
    from fastapi import HTTPException

    item = InventoryItemCreate(name="Widget", quantity=10, price=5.0)
    create_inventory_item(db_session, item)
    with pytest.raises(HTTPException) as exc_info:
        create_inventory_item(db_session, item)
    assert exc_info.value.status_code == 400
    assert "already exists" in str(exc_info.value.detail)

def test_get_all_inventory_items_empty(db_session):
    from services import get_all_inventory_items
    items = get_all_inventory_items(db_session)
    assert isinstance(items, list)
    assert len(items) == 0

def test_get_all_inventory_items_with_items(db_session):
    from services import create_inventory_item, get_all_inventory_items
    from schemas import InventoryItemCreate

    create_inventory_item(db_session, InventoryItemCreate(name="A", quantity=1, price=1.0))
    create_inventory_item(db_session, InventoryItemCreate(name="B", quantity=2, price=2.0))
    results = get_all_inventory_items(db_session)
    assert {item.name for item in results} == {"A", "B"}

def test_update_inventory_item_quantity_success(db_session):
    from services import create_inventory_item, update_inventory_item_quantity
    from schemas import InventoryItemCreate

    item = create_inventory_item(db_session, InventoryItemCreate(name="Upd", quantity=5, price=2.0))
    updated = update_inventory_item_quantity(db_session, item.id, 77)
    assert updated.id == item.id
    assert updated.quantity == 77

def test_update_inventory_item_quantity_not_found(db_session):
    from services import update_inventory_item_quantity
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc_info:
        update_inventory_item_quantity(db_session, "does-not-exist", 10)
    assert exc_info.value.status_code == 404
    assert "not found" in str(exc_info.value.detail).lower()

def test_delete_inventory_item_success(db_session):
    from services import create_inventory_item, delete_inventory_item
    from schemas import InventoryItemCreate

    item = create_inventory_item(db_session, InventoryItemCreate(name="Del", quantity=4, price=1.0))
    delete_inventory_item(db_session, item.id)
    # Should no longer exist
    remaining = db_session.query(InventoryItem).filter_by(id=item.id).first()
    assert remaining is None

def test_delete_inventory_item_not_found(db_session):
    from services import delete_inventory_item
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc_info:
        delete_inventory_item(db_session, "bad-id")
    assert exc_info.value.status_code == 404

# ---- API TESTS ----

def test_api_create_inventory_admin_success():
    app.dependency_overrides["get_current_user"] = get_admin_user
    data = {"name": "APIWidget", "quantity": 5, "price": 9.99}
    res = client.post("/api/inventory", json=data, headers=auth_headers("admin-token"))
    assert res.status_code == 201
    payload = res.json()
    assert payload["name"] == "APIWidget"
    assert payload["quantity"] == 5
    assert abs(payload["price"] - 9.99) < 1e-6
    assert "id" in payload

def test_api_create_inventory_nonadmin_forbidden():
    app.dependency_overrides["get_current_user"] = get_regular_user
    data = {"name": "UserWidget", "quantity": 1, "price": 1.0}
    res = client.post("/api/inventory", json=data, headers=auth_headers("user-token"))
    assert res.status_code == 403
    assert "Admin access required" in res.json()["detail"]

def test_api_create_inventory_duplicate():
    app.dependency_overrides["get_current_user"] = get_admin_user
    # create once
    res1 = client.post("/api/inventory", json={"name": "DupWidget", "quantity": 3, "price": 2.1}, headers=auth_headers("admin-token"))
    assert res1.status_code == 201
    # try duplicate
    res2 = client.post("/api/inventory", json={"name": "DupWidget", "quantity": 6, "price": 8.0}, headers=auth_headers("admin-token"))
    assert res2.status_code == 400
    assert "already exists" in res2.json()["detail"]

def test_api_get_all_inventory_items():
    app.dependency_overrides["get_current_user"] = get_admin_user
    # Ensure there are items
    client.post("/api/inventory", json={"name": "Item1", "quantity": 1, "price": 1.0}, headers=auth_headers("admin-token"))
    client.post("/api/inventory", json={"name": "Item2", "quantity": 2, "price": 2.0}, headers=auth_headers("admin-token"))
    res = client.get("/api/inventory", headers=auth_headers("admin-token"))
    assert res.status_code == 200
    items = res.json()
    names = {obj["name"] for obj in items}
    assert "Item1" in names and "Item2" in names

def test_api_update_inventory_quantity_success():
    app.dependency_overrides["get_current_user"] = get_admin_user
    # Create item
    res = client.post("/api/inventory", json={"name": "UpdAPI", "quantity": 7, "price": 1.1}, headers=auth_headers("admin-token"))
    item_id = res.json()["id"]
    patch = {"quantity": 88}
    res2 = client.patch(f"/api/inventory/{item_id}/quantity", params=patch, headers=auth_headers("admin-token"))
    assert res2.status_code == 200
    assert res2.json()["quantity"] == 88

def test_api_update_inventory_quantity_not_found():
    app.dependency_overrides["get_current_user"] = get_admin_user
    fake_id = "00000000-0000-0000-0000-000000000000"
    patch = {"quantity": 22}
    res = client.patch(f"/api/inventory/{fake_id}/quantity", params=patch, headers=auth_headers("admin-token"))
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()

def test_api_update_inventory_quantity_forbidden():
    app.dependency_overrides["get_current_user"] = get_regular_user
    # create as admin first
    app.dependency_overrides["get_current_user"] = get_admin_user
    res = client.post("/api/inventory", json={"name": "BadUserUpd", "quantity": 12, "price":14.2}, headers=auth_headers("admin-token"))
    item_id = res.json()["id"]
    # try patch as regular user
    app.dependency_overrides["get_current_user"] = get_regular_user
    res2 = client.patch(f"/api/inventory/{item_id}/quantity", params={"quantity": 1}, headers=auth_headers("user-token"))
    assert res2.status_code == 403

def test_api_delete_inventory_item_success():
    app.dependency_overrides["get_current_user"] = get_admin_user
    # Create item
    res = client.post("/api/inventory", json={"name": "DelAPI", "quantity": 13, "price":6.1}, headers=auth_headers("admin-token"))
    item_id = res.json()["id"]
    res2 = client.delete(f"/api/inventory/{item_id}", headers=auth_headers("admin-token"))
    assert res2.status_code == 204

def test_api_delete_inventory_item_not_found():
    app.dependency_overrides["get_current_user"] = get_admin_user
    fake_id = "00000000-0000-0000-0000-000000000000"
    res = client.delete(f"/api/inventory/{fake_id}", headers=auth_headers("admin-token"))
    assert res.status_code == 404

def test_api_delete_inventory_item_forbidden():
    app.dependency_overrides["get_current_user"] = get_admin_user
    # create as admin first
    res = client.post("/api/inventory", json={"name": "NoPermDel", "quantity": 8, "price":1.5}, headers=auth_headers("admin-token"))
    item_id = res.json()["id"]
    # try delete as regular user
    app.dependency_overrides["get_current_user"] = get_regular_user
    res2 = client.delete(f"/api/inventory/{item_id}", headers=auth_headers("user-token"))
    assert res2.status_code == 403

def test_api_auth_rejects_bad_token():
    res = client.get("/api/inventory", headers=auth_headers("invalid-token"))
    assert res.status_code == 401
    assert "Invalid authentication credentials" in res.json()["detail"]

# ---- EDGE CASES ----

def test_create_inventory_item_with_zero_quantity_and_price(db_session):
    from services import create_inventory_item
    from schemas import InventoryItemCreate

    item = InventoryItemCreate(name="ZeroItem", quantity=0, price=0)
    db_obj = create_inventory_item(db_session, item)
    assert db_obj.quantity == 0
    assert db_obj.price == 0

def test_api_create_inventory_negative_quantity_price_fails():
    app.dependency_overrides["get_current_user"] = get_admin_user
    # negative quantity
    res = client.post("/api/inventory", json={"name": "NegQ", "quantity": -1, "price": 1.0}, headers=auth_headers("admin-token"))
    assert res.status_code == 422
    # negative price
    res2 = client.post("/api/inventory", json={"name": "NegP", "quantity": 1, "price": -10.0}, headers=auth_headers("admin-token"))
    assert res2.status_code == 422

def test_api_update_inventory_quantity_negative_quantity_fails():
    app.dependency_overrides["get_current_user"] = get_admin_user
    res = client.post("/api/inventory", json={"name": "UpdNeg", "quantity": 4, "price":4.2}, headers=auth_headers("admin-token"))
    item_id = res.json()["id"]
    res2 = client.patch(f"/api/inventory/{item_id}/quantity", params={"quantity": -100}, headers=auth_headers("admin-token"))
    assert res2.status_code == 422  # schema validation error

def test_api_get_all_inventory_items_empty():
    app.dependency_overrides["get_current_user"] = get_admin_user
    # Start with a fresh DB
    # Drop and recreate all for an empty table
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    res = client.get("/api/inventory", headers=auth_headers("admin-token"))
    assert res.status_code == 200
    assert res.json() == []

def test_api_paths_invalid_id_format_returns_404_or_422():
    app.dependency_overrides["get_current_user"] = get_admin_user
    # PATCH with invalid id
    res = client.patch("/api/inventory/INVALID_ID/quantity", params={"quantity": 5}, headers=auth_headers("admin-token"))
    # Depending on FastAPI, invalid UUID-like strings as IDs may result in 404 or pass as string
    assert res.status_code in (404, 422)
    # DELETE with invalid id
    res2 = client.delete("/api/inventory/INVALID_ID", headers=auth_headers("admin-token"))
    assert res2.status_code in (404, 422)