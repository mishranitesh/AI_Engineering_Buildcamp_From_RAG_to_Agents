import pytest
from fastapi.testclient import TestClient
from main import app, InventoryService, ItemCreate

client = TestClient(app)

# ========== UNIT TESTS ==========

def test_inventory_add_and_get_item():
    service = InventoryService()
    item = ItemCreate(name="Widget", quantity=5, price=19.99)
    out = service.add_item(item)
    assert out["id"] in service._store
    assert out["name"] == "Widget"
    assert out["quantity"] == 5
    assert out["price"] == 19.99
    # Can retrieve by id
    retrieved = service.get_item(out["id"])
    assert retrieved == out

def test_inventory_get_all_items():
    service = InventoryService()
    item1 = ItemCreate(name="A", quantity=1, price=0.1)
    item2 = ItemCreate(name="B", quantity=2, price=2.2)
    res1 = service.add_item(item1)
    res2 = service.add_item(item2)
    all_items = service.get_all_items()
    assert len(all_items) == 2
    ids = [i['id'] for i in all_items]
    assert res1["id"] in ids and res2["id"] in ids

def test_inventory_update_quantity():
    service = InventoryService()
    item = ItemCreate(name="Update", quantity=1, price=0)
    out = service.add_item(item)
    updated = service.update_quantity(out["id"], 10)
    assert updated["quantity"] == 10
    # Non-existent id
    assert service.update_quantity("not-exists", 2) is None

def test_inventory_delete_item():
    service = InventoryService()
    item = ItemCreate(name="Del", quantity=1, price=1)
    out = service.add_item(item)
    assert service.delete_item(out["id"]) is True
    assert service.delete_item(out["id"]) is False  # Already gone

def test_inventory_get_item_not_found():
    service = InventoryService()
    assert service.get_item("nonexistent") is None

# ========== API TESTS ==========

def create_item_api(name="TestItem", quantity=3, price=4.2):
    payload = {"name": name, "quantity": quantity, "price": price}
    response = client.post("/items", json=payload)
    return response

def test_post_item_success():
    response = create_item_api("APIitem", 5, 12.75)
    assert response.status_code == 201
    out = response.json()
    assert out["name"] == "APIitem"
    assert out["quantity"] == 5
    assert out["price"] == 12.75
    assert "id" in out

def test_post_item_bad_payloads():
    # Blank name
    payload = {"name": "", "quantity": 3, "price": 1}
    r = client.post("/items", json=payload)
    assert r.status_code == 422
    # Zero quantity
    payload = {"name": "Bad", "quantity": 0, "price": 1}
    r = client.post("/items", json=payload)
    assert r.status_code == 422
    # Negative quantity
    payload = {"name": "Bad2", "quantity": -5, "price": 1}
    r = client.post("/items", json=payload)
    assert r.status_code == 422
    # Negative price
    payload = {"name": "Bad3", "quantity": 2, "price": -1}
    r = client.post("/items", json=payload)
    assert r.status_code == 422

def test_get_all_items_api():
    # Add two items
    r1 = create_item_api("Item1", 2, 9.9)
    r2 = create_item_api("Item2", 4, 99.0)
    get_resp = client.get("/items")
    assert get_resp.status_code == 200
    items = get_resp.json()
    names = [i["name"] for i in items]
    assert "Item1" in names
    assert "Item2" in names

def test_patch_update_quantity_success():
    post_resp = create_item_api("PatchMe", 6, 10.5)
    itemid = post_resp.json()["id"]
    patch_resp = client.patch(f"/items/{itemid}", json={"quantity": 44})
    assert patch_resp.status_code == 200
    out = patch_resp.json()
    assert out["quantity"] == 44
    assert out["name"] == "PatchMe"

def test_patch_update_quantity_notfound():
    bad_id = "00000000-0000-0000-0000-000000000000"
    patch_resp = client.patch(f"/items/{bad_id}", json={"quantity": 5})
    assert patch_resp.status_code == 404

def test_patch_update_quantity_bad_quantity():
    post_resp = create_item_api("PatchBad", 2, 1.1)
    itemid = post_resp.json()["id"]
    # Zero quantity
    patch_resp = client.patch(f"/items/{itemid}", json={"quantity": 0})
    assert patch_resp.status_code == 422
    # Negative quantity
    patch_resp = client.patch(f"/items/{itemid}", json={"quantity": -5})
    assert patch_resp.status_code == 422
    # Missing quantity
    patch_resp = client.patch(f"/items/{itemid}", json={})
    assert patch_resp.status_code == 422

def test_delete_item_success():
    post_resp = create_item_api("DeleteMe", 1, 1)
    itemid = post_resp.json()["id"]
    del_resp = client.delete(f"/items/{itemid}")
    assert del_resp.status_code == 200
    assert del_resp.json()["detail"] == "Item deleted"
    # Try deleting again
    del_resp2 = client.delete(f"/items/{itemid}")
    assert del_resp2.status_code == 404

def test_delete_item_not_found():
    bad_id = "deadbeef-dead-beef-dead-beefdeadbeef"
    del_resp = client.delete(f"/items/{bad_id}")
    assert del_resp.status_code == 404

# ========== EDGE CASES ==========

def test_post_item_strip_whitespace_name():
    resp = create_item_api("   whitespace   ", 7, 2.5)
    assert resp.status_code == 201
    out = resp.json()
    assert out["name"] == "whitespace"

def test_inventory_duplicate_names():
    # API does not enforce unique names, should allow duplicates
    resp1 = create_item_api("dupe", 1, 1.0)
    resp2 = create_item_api("dupe", 2, 2.0)
    out1, out2 = resp1.json(), resp2.json()
    assert out1["id"] != out2["id"]
    assert out1["name"] == out2["name"]

def test_empty_get_items_returns_list():
    # Should return a list, not an object
    # We'll create a new app for isolation
    from main import InventoryService as ServiceClass
    service = ServiceClass()
    assert service.get_all_items() == []