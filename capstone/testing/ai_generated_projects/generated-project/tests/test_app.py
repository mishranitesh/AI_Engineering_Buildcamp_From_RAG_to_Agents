import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from main import app, get_db
from models import Base, InventoryItem
from services import (
    create_inventory_item,
    get_all_inventory_items,
    update_inventory_item_quantity,
    delete_inventory_item,
)
from schemas import (
    InventoryItemCreate,
    InventoryItemUpdateQuantity,
)
from fastapi import status, HTTPException

# Create a separate in-memory SQLite database for tests
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

# Dependency override for FastAPI
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


###########
# Unit Tests for service functions

@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        db.rollback()


def test_create_inventory_item_success(db_session):
    item_in = InventoryItemCreate(name="Widget", quantity=5, price=19.99)
    item = create_inventory_item(db_session, item_in)
    assert item.id is not None
    assert item.name == "Widget"
    assert item.quantity == 5
    assert float(item.price) == 19.99


def test_create_inventory_item_strips_whitespace(db_session):
    item_in = InventoryItemCreate(name="  Gadget ", quantity=10, price=9.99)
    item = create_inventory_item(db_session, item_in)
    assert item.name == "Gadget"


def test_get_all_inventory_items_empty(db_session):
    items = get_all_inventory_items(db_session)
    assert items == []


def test_get_all_inventory_items_non_empty(db_session):
    create_inventory_item(db_session, InventoryItemCreate(name="Product", quantity=2, price=4.20))
    items = get_all_inventory_items(db_session)
    assert isinstance(items, list)
    assert len(items) == 1
    assert items[0].name == "Product"


def test_update_inventory_item_quantity_success(db_session):
    item = create_inventory_item(db_session, InventoryItemCreate(name="ChangeMe", quantity=3, price=8.1))
    updated_item = update_inventory_item_quantity(db_session, item.id, 7)
    assert updated_item.quantity == 7


def test_update_inventory_item_quantity_to_zero(db_session):
    item = create_inventory_item(db_session, InventoryItemCreate(name="ZCount", quantity=5, price=22.5))
    updated_item = update_inventory_item_quantity(db_session, item.id, 0)
    assert updated_item.quantity == 0


def test_update_inventory_item_quantity_negative(db_session):
    item = create_inventory_item(db_session, InventoryItemCreate(name="NegativeTest", quantity=6, price=5.55))
    with pytest.raises(HTTPException) as excinfo:
        update_inventory_item_quantity(db_session, item.id, -3)
    assert excinfo.value.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_update_inventory_item_quantity_not_found(db_session):
    with pytest.raises(HTTPException) as excinfo:
        update_inventory_item_quantity(db_session, 9999, 10)
    assert excinfo.value.status_code == status.HTTP_404_NOT_FOUND


def test_delete_inventory_item_success(db_session):
    item = create_inventory_item(db_session, InventoryItemCreate(name="ToDelete", quantity=4, price=4.75))
    # Should not raise
    delete_inventory_item(db_session, item.id)
    all_ids = [i.id for i in get_all_inventory_items(db_session)]
    assert item.id not in all_ids


def test_delete_inventory_item_not_found(db_session):
    with pytest.raises(HTTPException) as excinfo:
        delete_inventory_item(db_session, 555)
    assert excinfo.value.status_code == status.HTTP_404_NOT_FOUND


##############
# API Tests

def test_add_inventory_item_success():
    response = client.post(
        "/inventory",
        json={"name": "APIWidget", "quantity": 8, "price": "15.00"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "APIWidget"
    assert data["quantity"] == 8
    assert float(data["price"]) == 15.00
    assert "id" in data


def test_add_inventory_item_missing_field():
    # No price
    response = client.post(
        "/inventory",
        json={"name": "MissingPrice", "quantity": 3}
    )
    assert response.status_code == 422  # Validation error


def test_add_inventory_item_negative_quantity():
    response = client.post(
        "/inventory",
        json={"name": "NegQty", "quantity": -2, "price": "10.00"}
    )
    assert response.status_code == 422  # Quantity must be >= 0


def test_add_inventory_item_zero_quantity():
    response = client.post(
        "/inventory",
        json={"name": "ZeroQty", "quantity": 0, "price": "2.00"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["quantity"] == 0


def test_get_inventory_items_empty(monkeypatch):
    # Patch the DB to be empty
    with TestingSessionLocal() as db:
        db.query(InventoryItem).delete()
        db.commit()
    response = client.get("/inventory")
    assert response.status_code == 200
    assert response.json() == []


def test_get_inventory_items_many():
    with TestingSessionLocal() as db:
        db.query(InventoryItem).delete()
        db.commit()
        create_inventory_item(db, InventoryItemCreate(name="ItemA", quantity=2, price=1.23))
        create_inventory_item(db, InventoryItemCreate(name="ItemB", quantity=5, price=7.89))
    response = client.get("/inventory")
    assert response.status_code == 200
    items = response.json()
    names = [item["name"] for item in items]
    assert "ItemA" in names and "ItemB" in names
    assert isinstance(items, list)
    assert len(items) >= 2


def test_patch_inventory_quantity_success():
    # Create an item
    response = client.post("/inventory", json={"name": "ToUpdate", "quantity": 2, "price": "4.00"})
    item_id = response.json()["id"]
    patch_resp = client.patch(f"/inventory/{item_id}/quantity", json={"quantity": 17})
    assert patch_resp.status_code == 200
    assert patch_resp.json()["quantity"] == 17


def test_patch_inventory_quantity_to_zero():
    response = client.post("/inventory", json={"name": "PatchToZero", "quantity": 5, "price": "8.25"})
    item_id = response.json()["id"]
    patch_resp = client.patch(f"/inventory/{item_id}/quantity", json={"quantity": 0})
    assert patch_resp.status_code == 200
    assert patch_resp.json()["quantity"] == 0


def test_patch_inventory_quantity_negative():
    response = client.post("/inventory", json={"name": "PatchNegative", "quantity": 2, "price": "6.50"})
    item_id = response.json()["id"]
    patch_resp = client.patch(f"/inventory/{item_id}/quantity", json={"quantity": -10})
    assert patch_resp.status_code == 422  # Pydantic validation error


def test_patch_inventory_quantity_not_found():
    patch_resp = client.patch("/inventory/99999/quantity", json={"quantity": 1})
    assert patch_resp.status_code == 404


def test_delete_inventory_success():
    response = client.post("/inventory", json={"name": "DeleteAPI", "quantity": 3, "price": "5.00"})
    item_id = response.json()["id"]
    del_resp = client.delete(f"/inventory/{item_id}")
    assert del_resp.status_code == 204
    # Now query, should not find it
    items_response = client.get("/inventory")
    ids = [item["id"] for item in items_response.json()]
    assert item_id not in ids


def test_delete_inventory_not_found():
    del_resp = client.delete("/inventory/99999")
    assert del_resp.status_code == 404


#############
# Edge Cases

def test_add_inventory_item_long_name():
    long_name = "A" * 1000
    response = client.post(
        "/inventory",
        json={"name": long_name, "quantity": 1, "price": "1.00"}
    )
    assert response.status_code == 201
    assert response.json()["name"] == long_name

def test_add_inventory_item_zero_price():
    response = client.post(
        "/inventory",
        json={"name": "Freebie", "quantity": 1, "price": "0.00"}
    )
    assert response.status_code == 201
    assert float(response.json()["price"]) == 0.0

def test_add_inventory_item_decimal_places():
    response = client.post(
        "/inventory",
        json={"name": "Precise", "quantity": 1, "price": "1.239"}
    )
    # Should round or reject; pydantic enforces decimal_places=2, so 1.239 is invalid
    assert response.status_code == 422

def test_patch_quantity_missing_field():
    response = client.post("/inventory", json={"name": "PatchField", "quantity": 3, "price": "2.00"})
    item_id = response.json()["id"]
    patch_resp = client.patch(f"/inventory/{item_id}/quantity", json={})
    assert patch_resp.status_code == 422  # Missing "quantity"