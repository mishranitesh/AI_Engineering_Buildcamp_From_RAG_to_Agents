import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

from main import (
    app, Base, InventoryItemDB, InventoryService,
    InventoryItemCreate, InventoryItemQuantityUpdate,
    get_db
)

# --- Test DB Setup ---
TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestSessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

# Override the get_db dependency to use the test DB
def override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

# Create tables for test DB
Base.metadata.create_all(bind=engine)

client = TestClient(app)

# --- Fixtures ---

@pytest.fixture(scope="function")
def db():
    Base.metadata.create_all(bind=engine)
    db = TestSessionLocal()
    yield db
    db.rollback()
    db.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def inventory_item(db):
    item = InventoryItemDB(
        id="test-id-1",
        name="Test Item",
        quantity=10,
        price=15.99
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item

# --- Unit Tests - InventoryService ---

def test_create_item(db):
    data = InventoryItemCreate(name="Widget", quantity=5, price=9.99)
    item = InventoryService.create_item(db, data)
    assert item.name == "Widget"
    assert item.quantity == 5
    assert float(item.price) == 9.99
    assert len(item.id) == 36

def test_get_items(db):
    assert InventoryService.get_items(db) == []
    data = InventoryItemCreate(name="Gizmo", quantity=3, price=2.50)
    InventoryService.create_item(db, data)
    items = InventoryService.get_items(db)
    assert len(items) == 1
    assert items[0].name == "Gizmo"

def test_update_quantity_success(db):
    item = InventoryService.create_item(db, InventoryItemCreate(name="A", quantity=2, price=2.2))
    updated = InventoryService.update_quantity(db, item.id, 8)
    assert updated.quantity == 8

def test_update_quantity_not_found(db):
    with pytest.raises(Exception) as exc:
        InventoryService.update_quantity(db, "non-existent-id", 3)
    assert exc.value.status_code == 404

def test_delete_item_success(db):
    item = InventoryService.create_item(db, InventoryItemCreate(name="B", quantity=5, price=10.0))
    # does not raise
    InventoryService.delete_item(db, item.id)
    items = InventoryService.get_items(db)
    assert all(i.id != item.id for i in items)

def test_delete_item_not_found(db):
    with pytest.raises(Exception) as exc:
        InventoryService.delete_item(db, "does-not-exist")
    assert exc.value.status_code == 404

# --- API Tests ---

def test_post_inventory_item():
    response = client.post("/api/inventory", json={
        "name": "Item1",
        "quantity": 7,
        "price": "12.50"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Item1"
    assert data["quantity"] == 7
    assert abs(data["price"] - 12.50) < 0.01
    assert len(data["id"]) == 36

def test_post_inventory_item_invalid_price():
    response = client.post("/api/inventory", json={
        "name": "Thing",
        "quantity": 1,
        "price": "0"
    })
    assert response.status_code == 422

def test_post_inventory_item_invalid_name():
    response = client.post("/api/inventory", json={
        "name": "",
        "quantity": 1,
        "price": "7.77"
    })
    assert response.status_code == 422

def test_list_inventory_items_empty():
    response = client.get("/api/inventory")
    assert response.status_code == 200
    assert response.json() == []

def test_list_inventory_items_with_data():
    item1 = client.post("/api/inventory", json={"name": "X", "quantity": 2, "price": "1.10"}).json()
    item2 = client.post("/api/inventory", json={"name": "Y", "quantity": 0, "price": "3.14"}).json()
    response = client.get("/api/inventory")
    assert response.status_code == 200
    items = response.json()
    assert any(i["id"] == item1["id"] for i in items)
    assert any(i["id"] == item2["id"] for i in items)

def test_update_inventory_quantity_success():
    item = client.post("/api/inventory", json={"name": "ToUpdate", "quantity": 9, "price": "5.00"}).json()
    response = client.put(
        f"/api/inventory/{item['id']}/quantity",
        json={"quantity": 15}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == item["id"]
    assert data["quantity"] == 15

def test_update_inventory_quantity_not_found():
    response = client.put(
        "/api/inventory/does-not-exist/quantity",
        json={"quantity": 11}
    )
    assert response.status_code == 404

def test_update_inventory_quantity_invalid():
    item = client.post("/api/inventory", json={"name": "ToUpd2", "quantity": 6, "price": "1.00"}).json()
    response = client.put(
        f"/api/inventory/{item['id']}/quantity",
        json={"quantity": -5}
    )
    assert response.status_code == 422

def test_delete_inventory_item_success():
    item = client.post("/api/inventory", json={"name": "ToDelete", "quantity": 11, "price": "15.33"}).json()
    response = client.delete(f"/api/inventory/{item['id']}")
    assert response.status_code == 204
    # Should not be present anymore
    items = client.get("/api/inventory").json()
    ids = [i["id"] for i in items]
    assert item["id"] not in ids

def test_delete_inventory_item_not_found():
    response = client.delete("/api/inventory/non-existent")
    assert response.status_code == 404

# --- Edge Cases ---

def test_create_item_large_quantity_and_price():
    response = client.post("/api/inventory", json={
        "name": "Biggie",
        "quantity": 999999999,
        "price": "99999999.99"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["quantity"] == 999999999
    assert abs(data["price"] - 99999999.99) < 0.01

def test_create_item_max_length_name():
    name = "x" * 128
    response = client.post("/api/inventory", json={
        "name": name,
        "quantity": 1,
        "price": "1.00"
    })
    assert response.status_code == 201
    assert response.json()["name"] == name

def test_create_item_too_long_name():
    name = "x" * 129
    response = client.post("/api/inventory", json={
        "name": name,
        "quantity": 1,
        "price": "1.00"
    })
    assert response.status_code == 422

def test_create_item_zero_quantity():
    response = client.post("/api/inventory", json={
        "name": "zeroQ",
        "quantity": 0,
        "price": "3.33"
    })
    assert response.status_code == 201
    assert response.json()["quantity"] == 0

def test_update_quantity_to_zero():
    item = client.post("/api/inventory", json={
        "name": "stock",
        "quantity": 10,
        "price": "2.22"
    }).json()
    response = client.put(f"/api/inventory/{item['id']}/quantity", json={"quantity": 0})
    assert response.status_code == 200
    assert response.json()["quantity"] == 0