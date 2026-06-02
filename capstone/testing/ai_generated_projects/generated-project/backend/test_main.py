import pytest
from fastapi.testclient import TestClient
from main import app, inventory_store, next_id

client = TestClient(app)

@pytest.fixture(autouse=True)
def clear_inventory():
    global next_id
    inventory_store.clear()
    next_id = 1

def test_create_then_get_items():
    # Add an item
    resp = client.post("/items/", json={
        "name": "Widget",
        "quantity": 10,
        "price": 2.5
    })
    assert resp.status_code == 201
    item = resp.json()
    assert item["name"] == "Widget"
    assert item["quantity"] == 10
    assert item["price"] == 2.5
    assert "id" in item

    # Get all items
    resp = client.get("/items/")
    assert resp.status_code == 200
    items = resp.json()
    assert any(i["id"] == item["id"] for i in items)

def test_create_invalid_item():
    resp = client.post("/items/", json={"name": "", "quantity": -1, "price": -5})
    assert resp.status_code == 422

def test_update_item_quantity():
    # Create item
    resp = client.post("/items/", json={"name": "Phone", "quantity": 5, "price": 499})
    assert resp.status_code == 201
    item_id = resp.json()["id"]

    # Update quantity (success)
    resp = client.put(f"/items/{item_id}/quantity/", json={"quantity": 12})
    assert resp.status_code == 200
    new_data = resp.json()
    assert new_data["id"] == item_id
    assert new_data["quantity"] == 12

    # Update with invalid quantity
    resp = client.put(f"/items/{item_id}/quantity/", json={"quantity": -3})
    assert resp.status_code == 422

    # Update non-existing
    resp = client.put(f"/items/999999/quantity/", json={"quantity": 1})
    assert resp.status_code == 404

def test_delete_item():
    # Create item
    resp = client.post("/items/", json={"name": "Book", "quantity": 2, "price": 12.99})
    assert resp.status_code == 201
    item_id = resp.json()["id"]

    # Delete it
    resp = client.delete(f"/items/{item_id}/")
    assert resp.status_code == 200
    assert resp.json()["message"].startswith("Item deleted")

    # Delete again (should 404)
    resp = client.delete(f"/items/{item_id}/")
    assert resp.status_code == 404