import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

import main
import services
import models

client = TestClient(main.app)

# --------- UNIT TESTS for services.py ---------
@pytest.fixture(autouse=True)
def clear_store():
    # Setup: Clear the inventory store before each test
    services._inventory_store.clear()

def test_add_item_and_list_items_unit():
    item_data = models.ItemCreate(name="Widget", quantity=10, price=2.5)
    result = services.add_item(item_data)
    assert isinstance(result, models.ItemResponse)
    assert result.name == "Widget"
    assert result.quantity == 10
    assert result.price == 2.5
    # Check that the item is in the store
    items = services.list_items()
    assert items == [result]

def test_update_item_quantity_success_unit():
    item_data = models.ItemCreate(name="Gadget", quantity=8, price=1.1)
    added = services.add_item(item_data)
    updated = services.update_item_quantity(added.id, 3)
    assert updated is not None
    assert updated.quantity == 3
    assert updated.id == added.id

def test_update_item_quantity_nonexistent_unit():
    updated = services.update_item_quantity("not_a_real_id", 5)
    assert updated is None

def test_delete_item_success_unit():
    item = services.add_item(models.ItemCreate(name="A", quantity=1, price=1.0))
    assert services.delete_item(item.id) is True
    assert item.id not in services._inventory_store

def test_delete_item_not_found_unit():
    assert services.delete_item("no-such-uuid") is False

def test_list_items_empty_unit():
    result = services.list_items()
    assert result == []

def test_add_multiple_items_unit():
    item1 = services.add_item(models.ItemCreate(name="A", quantity=1, price=1.0))
    item2 = services.add_item(models.ItemCreate(name="B", quantity=2, price=2.0))
    items = services.list_items()
    assert len(items) == 2
    ids = {item.id for item in items}
    assert item1.id in ids and item2.id in ids

# --------- UNIT TESTS for models.py ---------
def test_item_create_validation():
    # Normal entry
    models.ItemCreate(name="Name", quantity=0, price=0)
    # Negative cases
    with pytest.raises(ValidationError):
        models.ItemCreate(name="", quantity=1, price=1.0)
    with pytest.raises(ValidationError):
        models.ItemCreate(name="N", quantity=-1, price=1.0)
    with pytest.raises(ValidationError):
        models.ItemCreate(name="N", quantity=1, price=-0.1)

def test_item_update_quantity_validation():
    models.ItemUpdateQuantity(quantity=0)
    with pytest.raises(ValidationError):
        models.ItemUpdateQuantity(quantity=-5)

# --------- API TESTS for main.py ---------
def test_create_item_api():
    resp = client.post("/items", json={"name": "Book", "quantity": 10, "price": 9.99})
    assert resp.status_code == 201
    data = resp.json()
    assert "id" in data and data["name"] == "Book"
    assert data["quantity"] == 10
    assert data["price"] == 9.99

def test_create_item_api_invalid():
    resp = client.post("/items", json={"name": "", "quantity": 5, "price": 1.0})
    assert resp.status_code == 422  # Validation error for empty name

    resp = client.post("/items", json={"name": "Bad", "quantity": -1, "price": 1.0})
    assert resp.status_code == 422  # Validation error for negative quantity

    resp = client.post("/items", json={"name": "Bad", "quantity": 1, "price": -1.0})
    assert resp.status_code == 422  # Validation error for negative price

def test_get_all_items_api():
    # Add two items
    item1 = client.post("/items", json={"name": "Pen", "quantity": 3, "price": 0.99}).json()
    item2 = client.post("/items", json={"name": "Pencil", "quantity": 7, "price": 0.39}).json()
    resp = client.get("/items")
    assert resp.status_code == 200
    result = resp.json()
    names = {item['name'] for item in result}
    assert "Pen" in names and "Pencil" in names
    assert set(item['id'] for item in result) == {item1['id'], item2['id']}

def test_patch_item_quantity_api():
    # Add an item, then update quantity
    added = client.post("/items", json={"name": "Laptop", "quantity": 4, "price": 499.99}).json()
    item_id = added['id']
    resp = client.patch(f"/items/{item_id}", json={"quantity": 2})
    assert resp.status_code == 200
    assert resp.json()["quantity"] == 2

def test_patch_item_quantity_not_found_api():
    resp = client.patch("/items/nonexistent-id", json={"quantity": 10})
    assert resp.status_code == 404
    assert resp.json() == {"detail": "Item not found"}

def test_patch_item_quantity_invalid_api():
    added = client.post("/items", json={"name": "Chair", "quantity": 6, "price": 23.50}).json()
    item_id = added["id"]
    resp = client.patch(f"/items/{item_id}", json={"quantity": -3})
    assert resp.status_code == 422  # Validation error

def test_delete_item_api():
    added = client.post("/items", json={"name": "DeleteMe", "quantity": 1, "price": 1.0}).json()
    item_id = added["id"]
    resp = client.delete(f"/items/{item_id}")
    assert resp.status_code == 200
    assert resp.json() == {"detail": "Item deleted"}
    # Ensure that item is actually gone
    resp2 = client.delete(f"/items/{item_id}")
    assert resp2.status_code == 404

def test_delete_item_not_found_api():
    resp = client.delete("/items/someNonexistentUUID")
    assert resp.status_code == 404
    assert resp.json() == {"detail": "Item not found"}

# --------- EDGE CASES ---------
def test_add_item_with_zero_quantity_and_price():
    resp = client.post("/items", json={"name": "ZeroItem", "quantity": 0, "price": 0})
    assert resp.status_code == 201
    data = resp.json()
    assert data['quantity'] == 0 and data['price'] == 0.0

def test_update_quantity_to_zero():
    added = client.post("/items", json={"name": "ReduceToZero", "quantity": 5, "price": 1.01}).json()
    item_id = added["id"]
    resp = client.patch(f"/items/{item_id}", json={"quantity": 0})
    assert resp.status_code == 200
    assert resp.json()["quantity"] == 0

def test_update_with_large_quantity():
    large_qty = 10**9
    added = client.post("/items", json={"name": "Bulk", "quantity": 1, "price": 1.0}).json()
    resp = client.patch(f"/items/{added['id']}", json={"quantity": large_qty})
    assert resp.status_code == 200
    assert resp.json()["quantity"] == large_qty