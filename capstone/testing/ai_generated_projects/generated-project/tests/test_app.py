import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, clear_mappers

from main import (
    app, Base, InventoryCreate, InventoryUpdate,
    InventoryService, InventoryItem, get_db
)

# --------- Test database setup ---------
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

# Dependency override for tests
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

# --------- Unit tests for InventoryService ---------
@pytest.fixture
def session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Clean up for the next test
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)

def test_create_item_unit(session):
    service = InventoryService(session)
    create = InventoryCreate(name="Item A", quantity=10, price=19.99)
    item = service.create_item(create)
    assert item.id is not None
    assert item.name == "Item A"
    assert item.quantity == 10
    assert item.price == 19.99

def test_get_all_items_unit(session):
    service = InventoryService(session)
    service.create_item(InventoryCreate(name="Item X", quantity=4, price=2.5))
    service.create_item(InventoryCreate(name="Item Y", quantity=0, price=3.14))
    results = service.get_all_items()
    assert len(results) == 2
    names = [item.name for item in results]
    assert "Item X" in names and "Item Y" in names

def test_update_item_quantity_unit(session):
    service = InventoryService(session)
    item = service.create_item(InventoryCreate(name="Item Q", quantity=8, price=6.66))
    updated = service.update_item_quantity(item.id, 13)
    assert updated.quantity == 13
    # Negative/unchanged update should be enforced by validation layer not here

def test_update_item_quantity_not_found_unit(session):
    service = InventoryService(session)
    with pytest.raises(Exception) as excinfo:
        service.update_item_quantity(99999, 10)
    assert "Item not found" in str(excinfo.value)

def test_delete_item_unit(session):
    service = InventoryService(session)
    item = service.create_item(InventoryCreate(name="ToDelete", quantity=1, price=2.2))
    service.delete_item(item.id)
    # Now cannot find
    assert session.query(InventoryItem).filter_by(id=item.id).first() is None

def test_delete_item_not_found_unit(session):
    service = InventoryService(session)
    with pytest.raises(Exception) as excinfo:
        service.delete_item(12345)
    assert "Item not found" in str(excinfo.value)

# --------- API tests ---------
def test_create_inventory_item_api():
    res = client.post("/api/inventory", json={"name": "ApiWidget", "quantity": 77, "price": 123.45})
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "ApiWidget"
    assert data["quantity"] == 77
    assert data["price"] == 123.45
    assert isinstance(data["id"], int)

def test_create_inventory_item_api_validation():
    # Name too long
    res = client.post("/api/inventory", json={"name": "A" * 101, "quantity": 5, "price": 2.1})
    assert res.status_code == 422
    # Negative quantity
    res = client.post("/api/inventory", json={"name": "Widget", "quantity": -1, "price": 2.1})
    assert res.status_code == 422
    # Negative price
    res = client.post("/api/inventory", json={"name": "Widget", "quantity": 2, "price": -0.1})
    assert res.status_code == 422
    # Blank name
    res = client.post("/api/inventory", json={"name": "", "quantity": 2, "price": 0.0})
    assert res.status_code == 422

def test_list_inventory_items_api():
    # Add a couple first
    client.post("/api/inventory", json={"name": "Foo", "quantity": 1, "price": 0.99})
    client.post("/api/inventory", json={"name": "Bar", "quantity": 2, "price": 2.49})
    res = client.get("/api/inventory")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert any(item["name"] == "Foo" for item in data)
    assert any(item["name"] == "Bar" for item in data)

def test_update_inventory_quantity_api():
    # Create
    res = client.post("/api/inventory", json={"name": "ToPatch", "quantity": 5, "price": 10.0})
    item_id = res.json()["id"]

    # Valid patch
    resp2 = client.patch(f"/api/inventory/{item_id}", json={"quantity": 11})
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["quantity"] == 11

def test_update_inventory_quantity_not_found_api():
    res = client.patch("/api/inventory/999999", json={"quantity": 2})
    assert res.status_code == 404
    assert res.json()["detail"] == "Item not found"

def test_update_inventory_quantity_bad_validation_api():
    res = client.post("/api/inventory", json={"name": "PatchBad", "quantity": 3, "price": 1.2})
    item_id = res.json()["id"]
    res2 = client.patch(f"/api/inventory/{item_id}", json={"quantity": -5})
    assert res2.status_code == 422

def test_delete_inventory_item_api():
    # Add one to delete
    res = client.post("/api/inventory", json={"name": "GoneSoon", "quantity": 1, "price": 50.0})
    item_id = res.json()["id"]
    delres = client.delete(f"/api/inventory/{item_id}")
    assert delres.status_code == 204
    # Now verify gone
    getres = client.get("/api/inventory")
    names = [obj["name"] for obj in getres.json()]
    assert "GoneSoon" not in names

def test_delete_inventory_item_not_found_api():
    delres = client.delete("/api/inventory/123456")
    assert delres.status_code == 404
    assert delres.json()["detail"] == "Item not found"

def test_list_inventory_items_empty_api():
    # Clear all items first
    session = next(override_get_db())
    session.query(InventoryItem).delete()
    session.commit()
    res = client.get("/api/inventory")
    assert res.status_code == 200
    assert res.json() == []

# --------- Edge cases ---------
def test_create_and_strip_name_api():
    res = client.post("/api/inventory", json={"name": "   with spaces   ", "quantity": 1, "price": 2.2})
    assert res.status_code == 201
    assert res.json()["name"] == "with spaces"

def test_large_quantity_and_price_values_api():
    big_qty = 1_000_000_000
    big_price = 123456789.123456
    res = client.post("/api/inventory", json={"name": "BigVals", "quantity": big_qty, "price": big_price})
    assert res.status_code == 201
    data = res.json()
    assert data["quantity"] == big_qty
    assert data["price"] == big_price

def test_update_to_zero_quantity_api():
    res = client.post("/api/inventory", json={"name": "StockOut", "quantity": 7, "price": 9.99})
    item_id = res.json()["id"]
    res2 = client.patch(f"/api/inventory/{item_id}", json={"quantity": 0})
    assert res2.status_code == 200
    assert res2.json()["quantity"] == 0