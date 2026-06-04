import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from main import (
    app, Base, InventoryRepository, InventoryService,
    InventoryCreateRequest, UpdateQuantityRequest, InventoryItem
)

# ----------------------
# ---- DB FIXTURES -----
# ----------------------

# Use a separate in-memory database for testing
TEST_DB_URL = "sqlite:///:memory:"

@pytest.fixture(scope="function")
def db_session():
    engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def repo(db_session):
    return InventoryRepository(db_session)

@pytest.fixture(scope="function")
def service(repo):
    return InventoryService(repo)

@pytest.fixture(scope="function")
def client(monkeypatch):
    engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    Base.metadata.create_all(bind=engine)
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()
    app.dependency_overrides = {}
    from main import get_db
    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides = {}

# ----------------------
# -- UNIT TESTS -------
# ----------------------

def test_repo_create_and_get_item(repo):
    item = repo.create(name="Widget", quantity=10, price=9.99)
    assert item.id > 0
    assert item.name == "Widget"
    assert item.quantity == 10
    assert float(item.price) == 9.99

    fetched = repo.get(item.id)
    assert fetched is not None
    assert fetched.id == item.id

def test_repo_list_items(repo):
    repo.create(name="A", quantity=1, price=1.5)
    repo.create(name="B", quantity=2, price=2.5)
    items = repo.list()
    assert len(items) == 2
    names = {it.name for it in items}
    assert {"A", "B"} == names

def test_repo_update_quantity(repo):
    item = repo.create(name="A", quantity=2, price=2.5)
    updated = repo.update_quantity(item.id, 5)
    assert updated.quantity == 5
    # Non-existing item
    none = repo.update_quantity(999, 10)
    assert none is None

def test_repo_delete(repo):
    item = repo.create(name="A", quantity=2, price=2.5)
    result = repo.delete(item.id)
    assert result is True
    # Idempotent: deleting again
    result2 = repo.delete(item.id)
    assert result2 is False

def test_service_add_item(service):
    req = InventoryCreateRequest(name="Test", quantity=4, price=12.23)
    obj = service.add_item(req)
    assert obj.id
    assert obj.name == "Test"
    assert obj.quantity == 4
    assert float(obj.price) == 12.23

def test_service_add_item_trim_name(service):
    req = InventoryCreateRequest(name="  Space  ", quantity=4, price=12.23)
    obj = service.add_item(req)
    # Should strip whitespace in name
    assert obj.name == "Space"

def test_service_update_item_quantity(service):
    add = InventoryCreateRequest(name="Test", quantity=4, price=1.00)
    obj = service.add_item(add)
    updated = service.update_item_quantity(obj.id, 99)
    assert updated.quantity == 99

def test_service_update_item_quantity_invalid_id(service):
    with pytest.raises(Exception) as excinfo:
        service.update_item_quantity(9999, 1)
    assert excinfo.value.status_code == 404

def test_service_update_item_quantity_negative(service):
    add = InventoryCreateRequest(name="Test", quantity=3, price=1.00)
    obj = service.add_item(add)
    with pytest.raises(Exception) as excinfo:
        service.update_item_quantity(obj.id, -1)
    assert excinfo.value.status_code == 400

def test_service_delete_item_success(service):
    req = InventoryCreateRequest(name="Test", quantity=2, price=2)
    obj = service.add_item(req)
    # Should not raise
    service.delete_item(obj.id)
    # Should now raise 404
    with pytest.raises(Exception) as excinfo:
        service.delete_item(obj.id)
    assert excinfo.value.status_code == 404

# ----------------------
# -- API TESTS ---------
# ----------------------

def test_api_add_and_list_inventory(client):
    payload = {"name": "Pencil", "quantity": 120, "price": 0.49}
    resp = client.post("/inventory", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Pencil"
    assert data["quantity"] == 120
    assert data["price"] == "0.49"

    resp_list = client.get("/inventory")
    assert resp_list.status_code == 200
    items = resp_list.json()
    assert isinstance(items, list)
    assert any(item["name"] == "Pencil" for item in items)

def test_api_add_inventory_invalid_data(client):
    # Empty name
    payload = {"name": "", "quantity": 2, "price": 5.0}
    resp = client.post("/inventory", json=payload)
    assert resp.status_code == 422

    # Negative quantity
    payload2 = {"name": "Test", "quantity": -10, "price": 5.0}
    resp2 = client.post("/inventory", json=payload2)
    assert resp2.status_code == 422

    # Zero or negative price
    payload3 = {"name": "Test", "quantity": 5, "price": 0}
    resp3 = client.post("/inventory", json=payload3)
    assert resp3.status_code == 422

def test_api_update_inventory_quantity(client):
    payload = {"name": "Notebook", "quantity": 33, "price": 3.50}
    resp = client.post("/inventory", json=payload)
    item_id = resp.json()["id"]

    resp_update = client.put(f"/inventory/{item_id}/quantity", json={"quantity": 77})
    assert resp_update.status_code == 200
    upd = resp_update.json()
    assert upd["quantity"] == 77
    assert upd["id"] == item_id

def test_api_update_inventory_quantity_negative(client):
    payload = {"name": "NegativeTest", "quantity": 2, "price": 1.10}
    resp = client.post("/inventory", json=payload)
    item_id = resp.json()["id"]

    resp_update = client.put(f"/inventory/{item_id}/quantity", json={"quantity": -3})
    assert resp_update.status_code == 422

def test_api_update_inventory_nonexistent(client):
    resp_update = client.put(f"/inventory/12345/quantity", json={"quantity": 4})
    assert resp_update.status_code == 404

def test_api_delete_inventory_item(client):
    payload = {"name": "DelTest", "quantity": 8, "price": 8.0}
    resp = client.post("/inventory", json=payload)
    item_id = resp.json()["id"]

    resp_delete = client.delete(f"/inventory/{item_id}")
    assert resp_delete.status_code == 204

    # Delete again: should be 404
    resp_delete2 = client.delete(f"/inventory/{item_id}")
    assert resp_delete2.status_code == 404

def test_api_delete_nonexistent(client):
    resp = client.delete("/inventory/987654")
    assert resp.status_code == 404

def test_api_list_inventory_empty(client):
    # Should start empty
    resp = client.get("/inventory")
    assert resp.status_code == 200
    assert resp.json() == []

def test_api_get_with_invalid_item_id(client):
    # Invalid (negative) id at update
    resp = client.put("/inventory/-10/quantity", json={"quantity": 1})
    assert resp.status_code == 422
    resp = client.delete("/inventory/-1")
    assert resp.status_code == 422