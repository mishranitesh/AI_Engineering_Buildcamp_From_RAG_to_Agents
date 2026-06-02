import pytest
from fastapi.testclient import TestClient
from main import app, add_inventory_item, get_all_inventory_items, update_inventory_item_quantity, delete_inventory_item, InventoryItemCreate, inventory_store

client = TestClient(app)

@pytest.fixture(autouse=True)
def clear_inventory():
    # Clear inventory _before_ each test (not thread-safe, but okay here)
    inventory_store.clear()

# -------------------------- UNIT TESTS --------------------------

def test_add_inventory_item_unit():
    dto = InventoryItemCreate(name="Test Item", quantity=1, price=5.0)
    item = add_inventory_item(dto)
    assert item.name == "Test Item"
    assert item.quantity == 1
    assert item.price == 5.0
    assert item.id in inventory_store

def test_update_inventory_item_quantity_unit():
    dto = InventoryItemCreate(name="Test Unit", quantity=6, price=3.3)
    item = add_inventory_item(dto)
    updated = update_inventory_item_quantity(item.id, 99)
    assert updated.quantity == 99
    assert inventory_store[item.id].quantity == 99

def test_update_inventory_item_quantity_404_unit():
    with pytest.raises(Exception):
        update_inventory_item_quantity(9999999, 10)

def test_delete_inventory_item_unit():
    dto = InventoryItemCreate(name="ToDelete", quantity=4, price=2.1)
    item = add_inventory_item(dto)
    delete_inventory_item(item.id)
    assert item.id not in inventory_store

def test_delete_inventory_item_404_unit():
    with pytest.raises(Exception):
        delete_inventory_item(93939393)

def test_get_all_inventory_items_unit():
    dto1 = InventoryItemCreate(name="A", quantity=1, price=0.5)
    dto2 = InventoryItemCreate(name="B", quantity=2, price=1.5)
    add_inventory_item(dto1)
    add_inventory_item(dto2)
    all_items = get_all_inventory_items()
    assert isinstance(all_items, list)
    names = [i.name for i in all_items]
    assert "A" in names and "B" in names

# ------------------- API TESTS (INTEGRATION) -------------------

def test_api_create_item_and_get_all():
    data = {"name": "Laptop", "quantity": 7, "price": 999.99}
    resp = client.post("/items/", json=data)
    assert resp.status_code == 201
    d = resp.json()
    assert d["name"] == "Laptop"
    assert isinstance(d["id"], int)
    # get all
    resp2 = client.get("/items/")
    assert resp2.status_code == 200
    found = any(x["id"] == d["id"] for x in resp2.json())
    assert found

def test_api_create_item_validation():
    # Blank name (only spaces)
    resp = client.post("/items/", json={"name": "  ", "quantity": 1, "price": 2.0})
    assert resp.status_code == 422
    
    # Negative quantity
    resp2 = client.post("/items/", json={"name": "Bad", "quantity": -2, "price": 2.0})
    assert resp2.status_code == 422
    
    # Negative price
    resp3 = client.post("/items/", json={"name": "Bad", "quantity": 2, "price": -6.0})
    assert resp3.status_code == 422

    # Missing field
    resp4 = client.post("/items/", json={"name": "Missing", "quantity": 1})
    assert resp4.status_code == 422

def test_api_update_quantity():
    # Make an item
    resp = client.post("/items/", json={"name": "Tablet", "quantity": 2, "price": 111.3})
    assert resp.status_code == 201
    item_id = resp.json()["id"]

    # Update quantity
    resp2 = client.put(f"/items/{item_id}/quantity/", json={"quantity": 44})
    assert resp2.status_code == 200
    assert resp2.json()["quantity"] == 44

    # Quantity: negative (should 422)
    resp3 = client.put(f"/items/{item_id}/quantity/", json={"quantity": -10})
    assert resp3.status_code == 422

    # Non-existent item
    resp4 = client.put(f"/items/123456789/quantity/", json={"quantity": 1})
    assert resp4.status_code == 404

    # Missing field
    resp5 = client.put(f"/items/{item_id}/quantity/", json={})
    assert resp5.status_code == 422

def test_api_delete_item():
    # Create item
    resp = client.post("/items/", json={"name": "Book", "quantity": 2, "price": 12.99})
    assert resp.status_code == 201
    item_id = resp.json()["id"]
    # Delete it
    resp = client.delete(f"/items/{item_id}/")
    assert resp.status_code == 200
    assert resp.json()["message"] == "Item deleted successfully"
    # Try again: 404
    resp = client.delete(f"/items/{item_id}/")
    assert resp.status_code == 404

def test_api_list_items_empty():
    resp = client.get("/items/")
    assert resp.status_code == 200
    assert resp.json() == []

# --------------------- EDGE CASES ------------------------

def test_api_long_name_and_large_numbers():
    # Long name, big numbers
    long_name = "X" * 1000
    resp = client.post("/items/", json={
        "name": long_name, "quantity": 10000000, "price": 99999999.99
    })
    assert resp.status_code == 201
    result = resp.json()
    assert result["name"] == long_name
    assert result["quantity"] == 10000000
    assert result["price"] == 99999999.99

def test_quantity_zero_allowed():
    resp = client.post("/items/", json={"name": "Zero", "quantity": 0, "price": 1.2})
    assert resp.status_code == 201
    assert resp.json()["quantity"] == 0
    # Update to 0
    item_id = resp.json()["id"]
    resp2 = client.put(f"/items/{item_id}/quantity/", json={"quantity": 0})
    assert resp2.status_code == 200
    assert resp2.json()["quantity"] == 0

def test_create_with_minimum_fields():
    resp = client.post("/items/", json={"name": "A", "quantity": 0, "price": 0})
    assert resp.status_code == 201
    d = resp.json()
    assert d["name"] == "A"
    assert d["quantity"] == 0
    assert d["price"] == 0.0

def test_consecutive_ids_unique():
    resp1 = client.post("/items/", json={"name": "Item1", "quantity": 1, "price": 10})
    resp2 = client.post("/items/", json={"name": "Item2", "quantity": 2, "price": 20})
    id1 = resp1.json()["id"]
    id2 = resp2.json()["id"]
    assert id1 != id2
    assert isinstance(id1, int) and isinstance(id2, int)