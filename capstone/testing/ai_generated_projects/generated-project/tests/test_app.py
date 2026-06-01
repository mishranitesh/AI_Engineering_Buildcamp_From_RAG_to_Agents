import pytest
from fastapi.testclient import TestClient
from uuid import uuid4, UUID

from main import app, InventoryService, InventoryItemCreate, inventory_items, name_index

client = TestClient(app)

@pytest.fixture(autouse=True)
def clear_storage():
    inventory_items.clear()
    name_index.clear()
    yield
    inventory_items.clear()
    name_index.clear()

# ---------- UNIT TESTS ----------

def test_add_item_unit():
    item = InventoryItemCreate(name="Widget", quantity=5, price=12.25)
    out = InventoryService.add_item(item)
    assert out.name == "Widget"
    assert out.quantity == 5
    assert out.price == 12.25
    assert out.id in inventory_items

def test_add_item_duplicate_name():
    item1 = InventoryItemCreate(name="Widget", quantity=1, price=2)
    item2 = InventoryItemCreate(name="widget", quantity=2, price=4)
    InventoryService.add_item(item1)
    with pytest.raises(Exception) as exc:
        InventoryService.add_item(item2)
    assert "Name must be unique" in str(exc.value)

def test_list_items_empty():
    assert InventoryService.list_items() == []

def test_get_item_by_id_not_found():
    fake_id = uuid4()
    with pytest.raises(Exception) as exc:
        InventoryService.get_item_by_id(fake_id)
    assert "Item not found" in str(exc.value)

def test_update_quantity_unit():
    item = InventoryItemCreate(name="Prod", quantity=3, price=2.1)
    out = InventoryService.add_item(item)
    updated = InventoryService.update_quantity(out.id, 12)
    assert updated.quantity == 12

def test_update_quantity_negative():
    item = InventoryItemCreate(name="Prod", quantity=3, price=2.1)
    out = InventoryService.add_item(item)
    with pytest.raises(Exception) as exc:
        InventoryService.update_quantity(out.id, -5)
    assert "non-negative" in str(exc.value)

def test_delete_item_unit():
    item = InventoryItemCreate(name="DeleteMe", quantity=1, price=1)
    out = InventoryService.add_item(item)
    InventoryService.delete_item(out.id)
    assert out.id not in inventory_items
    assert out.name.lower() not in name_index

def test_delete_item_not_found():
    with pytest.raises(Exception) as exc:
        InventoryService.delete_item(uuid4())
    assert "Item not found" in str(exc.value)

# ---------- API TESTS ----------

def test_create_item_api():
    resp = client.post("/items", json={"name": "Apple", "quantity": 10, "price": 2.99})
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Apple"
    assert data["quantity"] == 10
    assert data["price"] == 2.99
    assert "id" in data

def test_create_item_empty_name():
    resp = client.post("/items", json={"name": "", "quantity": 5, "price": 1.11})
    assert resp.status_code == 422  # pydantic validation error

def test_create_item_whitespace_name():
    resp = client.post("/items", json={"name": "   ", "quantity": 5, "price": 1.11})
    assert resp.status_code == 422  # validation error

def test_create_item_duplicate_case_insensitive():
    client.post("/items", json={"name": "Banana", "quantity": 1, "price": 0.1})
    resp = client.post("/items", json={"name": "BANANA", "quantity": 2, "price": 0.2})
    assert resp.status_code == 400
    assert "unique" in resp.json()["detail"]

def test_list_items_api_empty():
    resp = client.get("/items")
    assert resp.status_code == 200
    assert resp.json() == []

def test_list_items_api_some():
    client.post("/items", json={"name": "Orange", "quantity": 20, "price": 1.99})
    client.post("/items", json={"name": "Kiwi", "quantity": 3, "price": 0.99})
    resp = client.get("/items")
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) == 2
    assert {item["name"] for item in items} == {"Orange", "Kiwi"}

def test_update_quantity_api():
    resp = client.post("/items", json={"name": "Pear", "quantity": 1, "price": 0.5})
    iid = resp.json()["id"]
    patch = client.patch(f"/items/{iid}/quantity", json={"quantity": 5})
    assert patch.status_code == 200
    data = patch.json()
    assert data["quantity"] == 5

def test_update_quantity_not_found():
    fake_id = str(uuid4())
    resp = client.patch(f"/items/{fake_id}/quantity", json={"quantity": 7})
    assert resp.status_code == 404

def test_update_quantity_negative_api():
    resp = client.post("/items", json={"name": "Lettuce", "quantity": 3, "price": 2.0})
    iid = resp.json()["id"]
    patch = client.patch(f"/items/{iid}/quantity", json={"quantity": -1})
    assert patch.status_code == 422  # FastAPI returns 422 for body validation

def test_update_quantity_missing_quantity():
    resp = client.post("/items", json={"name": "Nuts", "quantity": 4, "price": 3.0})
    iid = resp.json()["id"]
    patch = client.patch(f"/items/{iid}/quantity", json={})
    assert patch.status_code == 422  # Pydantic validation on required field

def test_delete_item_api():
    resp = client.post("/items", json={"name": "ToDelete", "quantity": 7, "price": 7.7})
    iid = resp.json()["id"]
    resp_del = client.delete(f"/items/{iid}")
    assert resp_del.status_code == 204

    # Should not be able to get the item anymore (list should be empty)
    resp_get = client.get("/items")
    names = [d["name"] for d in resp_get.json()]
    assert "ToDelete" not in names

def test_delete_item_not_exist_api():
    resp = client.delete(f"/items/{uuid4()}")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Item not found."

# ---------- EDGE CASES ----------

def test_name_strip_uniqueness():
    # " Test " and "test" should be considered the same for uniqueness
    client.post("/items", json={"name": " Test ", "quantity": 1, "price": 1.0})
    resp = client.post("/items", json={"name": "test", "quantity":2, "price":2.0})
    assert resp.status_code == 400

def test_zero_quantity_and_price():
    resp = client.post("/items", json={"name": "Zero", "quantity": 0, "price": 0})
    assert resp.status_code == 201
    data = resp.json()
    assert data["quantity"] == 0
    assert data["price"] == 0

def test_large_values():
    resp = client.post("/items", json={"name": "Giant", "quantity": 10**6, "price": 99999999.99})
    assert resp.status_code == 201
    data = resp.json()
    assert data["quantity"] == 10**6
    assert abs(data["price"] - 99999999.99) < 0.01

def test_patch_invalid_uuid():
    resp = client.patch("/items/not-a-uuid/quantity", json={"quantity": 10})
    assert resp.status_code == 422  # Path param invalid UUID

def test_delete_invalid_uuid():
    resp = client.delete("/items/not-a-uuid")
    assert resp.status_code == 422