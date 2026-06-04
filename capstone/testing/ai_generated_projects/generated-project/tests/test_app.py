import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from main import app, get_db
from models import Base, InventoryItem
from services import (
    create_inventory_item,
    list_inventory_items,
    update_inventory_quantity,
    delete_inventory_item
)
from schemas import InventoryCreate, InventoryUpdateQuantity

from datetime import datetime

# --- Test DB Setup ---
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    yield db
    db.close()

# --- Unit Tests for Services ---

def test_create_inventory_item(db_session):
    item_data = InventoryCreate(name="Widget", quantity=10, price=1.99)
    item = create_inventory_item(db_session, item_data)
    assert item.id is not None
    assert item.name == "Widget"
    assert item.quantity == 10
    assert item.price == 1.99
    assert isinstance(item.created_at, datetime)

def test_list_inventory_items(db_session):
    create_inventory_item(db_session, InventoryCreate(name="A", quantity=1, price=0.5))
    create_inventory_item(db_session, InventoryCreate(name="B", quantity=2, price=1.5))
    items = list_inventory_items(db_session)
    assert len(items) >= 2
    names = [item.name for item in items]
    assert "A" in names and "B" in names

def test_update_inventory_quantity_existing(db_session):
    item = create_inventory_item(db_session, InventoryCreate(name="Test", quantity=5, price=3.2))
    updated = update_inventory_quantity(db_session, item.id, 15)
    assert updated.quantity == 15

def test_update_inventory_quantity_not_found(db_session):
    result = update_inventory_quantity(db_session, "nonexistent-id", 10)
    assert result is None

def test_delete_inventory_item_existing(db_session):
    item = create_inventory_item(db_session, InventoryCreate(name="DeleteMe", quantity=3, price=1.0))
    result = delete_inventory_item(db_session, item.id)
    assert result is True
    # Should be gone
    assert db_session.query(InventoryItem).filter(InventoryItem.id == item.id).first() is None

def test_delete_inventory_item_not_found(db_session):
    result = delete_inventory_item(db_session, "fake-id")
    assert result is False

# --- API Tests ---

def test_add_inventory(client):
    resp = client.post("/api/inventory", json={
        "name": "TestItem",
        "quantity": 100,
        "price": 9.99
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["id"]
    assert data["name"] == "TestItem"
    assert data["quantity"] == 100
    assert data["price"] == 9.99
    assert "created_at" in data

def test_add_inventory_invalid_data(client):
    # Negative quantity not allowed
    resp = client.post("/api/inventory", json={
        "name": "InvalidItem",
        "quantity": -1,
        "price": 9.99
    })
    assert resp.status_code == 422

    # Negative price not allowed
    resp2 = client.post("/api/inventory", json={
        "name": "InvalidItem",
        "quantity": 2,
        "price": -1.0
    })
    assert resp2.status_code == 422

    # Name empty string
    resp3 = client.post("/api/inventory", json={
        "name": "",
        "quantity": 2,
        "price": 1.0
    })
    assert resp3.status_code == 422

def test_get_all_inventory(client):
    # Make sure at least one item
    resp = client.post("/api/inventory", json={
        "name": "GetMe",
        "quantity": 8,
        "price": 2.5
    })
    assert resp.status_code == 201
    resp = client.get("/api/inventory")
    assert resp.status_code == 200
    items = resp.json()
    assert isinstance(items, list)
    assert any(item["name"] == "GetMe" for item in items)

def test_patch_inventory_success(client):
    post_resp = client.post("/api/inventory", json={
        "name": "PatchMe",
        "quantity": 20,
        "price": 4.5
    })
    item_id = post_resp.json()["id"]
    patch_resp = client.patch(f"/api/inventory/{item_id}", json={"quantity": 123})
    assert patch_resp.status_code == 200
    data = patch_resp.json()
    assert data["quantity"] == 123

def test_patch_inventory_not_found(client):
    resp = client.patch("/api/inventory/non-existent-id", json={"quantity": 99})
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Inventory item not found"

def test_patch_inventory_invalid_quantity(client):
    post_resp = client.post("/api/inventory", json={
        "name": "InvalidPatch",
        "quantity": 25,
        "price": 7.7
    })
    item_id = post_resp.json()["id"]
    # Negative quantity
    resp = client.patch(f"/api/inventory/{item_id}", json={"quantity": -5})
    assert resp.status_code == 422

def test_delete_inventory_success(client):
    post_resp = client.post("/api/inventory", json={
        "name": "DeleteMe2",
        "quantity": 5,
        "price": 11.0
    })
    item_id = post_resp.json()["id"]
    del_resp = client.delete(f"/api/inventory/{item_id}")
    assert del_resp.status_code == 204
    # Confirm it's gone
    get_resp = client.patch(f"/api/inventory/{item_id}", json={"quantity": 10})
    assert get_resp.status_code == 404

def test_delete_inventory_not_found(client):
    resp = client.delete("/api/inventory/no-such-id")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Inventory item not found"

# --- Edge Case Tests ---

def test_massive_quantity_and_price(client):
    resp = client.post("/api/inventory", json={
        "name": "BigNumbers",
        "quantity": 10**9,
        "price": 1e10
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["quantity"] == 10**9
    assert data["price"] == 1e10

def test_zero_quantity_and_price(client):
    resp = client.post("/api/inventory", json={
        "name": "ZeroCase",
        "quantity": 0,
        "price": 0.0
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["quantity"] == 0
    assert data["price"] == 0.0

def test_unicode_and_long_name(client):
    name = "商品アイテム" + "x"*90
    resp = client.post("/api/inventory", json={
        "name": name,
        "quantity": 2,
        "price": 4.0
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"].startswith("商品アイテム")
    assert len(data["name"]) == len(name)