import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, clear_mappers
from sqlalchemy.pool import StaticPool

from main import app, get_db
from models import Base, InventoryItem
from services import InventoryService

# Use an in-memory SQLite database for testing purposes
DATABASE_TEST_URL = "sqlite://"
engine = create_engine(
    DATABASE_TEST_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)

# Dependency override
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

#########
# UNIT TESTS (for service logic)
#########

@pytest.fixture
def db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()

def test_add_item_service(db):
    item_data = type('obj', (object,), {'name': 'Widget', 'quantity': 5, 'price': 9.99})()
    created = InventoryService.add_item(db, item_data)
    assert created.id is not None
    assert created.name == 'Widget'
    assert created.quantity == 5
    assert created.price == 9.99

def test_list_items_service(db):
    # Insert sample data
    InventoryService.add_item(db, type('obj', (object,), {'name': 'Thing', 'quantity': 2, 'price': 1.50})())
    items = InventoryService.list_items(db)
    assert isinstance(items, list)
    assert items[0].name == 'Thing'

def test_update_item_quantity_service(db):
    item = InventoryService.add_item(db, type('obj', (object,), {'name': 'Box', 'quantity': 10, 'price': 4.20})())
    updated = InventoryService.update_item_quantity(db, item.id, 20)
    assert updated.quantity == 20

def test_update_item_quantity_service_not_found(db):
    with pytest.raises(Exception) as excinfo:
        InventoryService.update_item_quantity(db, 9999, 10)
    assert excinfo.value.status_code == 404

def test_delete_item_service(db):
    item = InventoryService.add_item(db, type('obj', (object,), {'name': 'Bag', 'quantity': 8, 'price': 3.75})())
    InventoryService.delete_item(db, item.id)
    assert db.query(InventoryItem).filter_by(id=item.id).first() is None

def test_delete_item_service_not_found(db):
    with pytest.raises(Exception) as excinfo:
        InventoryService.delete_item(db, 7777)
    assert excinfo.value.status_code == 404

#########
# API TESTS (CRUD, edge & validation)
#########

def test_create_inventory_item():
    response = client.post("/inventory", json={"name": "Book", "quantity": 10, "price": 13.5})
    assert response.status_code == 201
    data = response.json()
    assert data["id"] > 0
    assert data["name"] == "Book"
    assert data["quantity"] == 10
    assert data["price"] == 13.5

def test_create_inventory_item_validation():
    # Negative quantity
    response = client.post("/inventory", json={"name": "Pencil", "quantity": -5, "price": 0.5})
    assert response.status_code == 422
    # Negative price
    response = client.post("/inventory", json={"name": "Ruler", "quantity": 3, "price": -0.1})
    assert response.status_code == 422
    # Name too long
    response = client.post("/inventory", json={"name": "X"*300, "quantity": 3, "price": 2.0})
    assert response.status_code == 422
    # Missing fields
    response = client.post("/inventory", json={"name": "Marker"})
    assert response.status_code == 422

def test_list_inventory_items():
    # Add two items
    client.post("/inventory", json={"name": "Pen", "quantity": 4, "price": 1.2})
    client.post("/inventory", json={"name": "Pencil", "quantity": 9, "price": 0.75})
    response = client.get("/inventory")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2
    assert any(item["name"] == "Pen" for item in data)

def test_update_inventory_item_quantity():
    resp = client.post("/inventory", json={"name": "Notebook", "quantity": 3, "price": 5.00})
    item_id = resp.json()["id"]
    response = client.patch(f"/inventory/{item_id}", json={"quantity": 7})
    assert response.status_code == 200
    data = response.json()
    assert data["quantity"] == 7

def test_update_inventory_item_quantity_not_found():
    response = client.patch("/inventory/99999", json={"quantity": 15})
    assert response.status_code == 404
    assert response.json()["detail"] == "Item not found"

def test_update_inventory_item_quantity_bad_input():
    resp = client.post("/inventory", json={"name": "Eraser", "quantity": 2, "price": 0.5})
    item_id = resp.json()["id"]
    # negative quantity
    response = client.patch(f"/inventory/{item_id}", json={"quantity": -3})
    assert response.status_code == 422
    # missing quantity
    response = client.patch(f"/inventory/{item_id}", json={})
    assert response.status_code == 422

def test_delete_inventory_item():
    resp = client.post("/inventory", json={"name": "Stapler", "quantity": 1, "price": 2.25})
    item_id = resp.json()["id"]
    response = client.delete(f"/inventory/{item_id}")
    assert response.status_code == 204
    # Ensure deleted
    response2 = client.get("/inventory")
    assert all(item["id"] != item_id for item in response2.json())

def test_delete_inventory_item_not_found():
    response = client.delete("/inventory/1234567")
    assert response.status_code == 404
    assert response.json()["detail"] == "Item not found"

#########
# EDGE CASES
#########

def test_large_quantity_and_price():
    response = client.post("/inventory", json={"name": "LargeWidget", "quantity": 10**9, "price": 1.5e6})
    assert response.status_code == 201
    data = response.json()
    assert data["quantity"] == 10**9
    assert data["price"] == 1.5e6

def test_empty_list_inventory():
    # Clear table
    db = next(override_get_db())
    db.query(InventoryItem).delete()
    db.commit()
    response = client.get("/inventory")
    assert response.status_code == 200
    assert response.json() == []