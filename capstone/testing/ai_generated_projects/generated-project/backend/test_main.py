from fastapi.testclient import TestClient
from main import app
import pytest

client = TestClient(app)

def create_sample_item():
    response = client.post(
        "/api/inventory",
        json={"name": "TestItem", "quantity": 30, "price": 7.5}
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]

def test_patch_with_no_body_returns_422():
    item_id = create_sample_item()
    response = client.patch(f"/api/inventory/{item_id}", data="")  # No JSON
    assert response.status_code == 422
    assert "detail" in response.json()

def test_patch_with_missing_quantity_field():
    item_id = create_sample_item()
    response = client.patch(f"/api/inventory/{item_id}", json={})
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    assert any(
        err["loc"][-1] == "quantity" and err["type"].startswith("value_error.missing") for err in data["detail"]
    )

def test_patch_with_extra_field():
    item_id = create_sample_item()
    response = client.patch(
        f"/api/inventory/{item_id}", json={"quantity": 20, "unexpected": "oops"}
    )
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    assert any(
        err["type"] == "value_error.extra" for err in data["detail"]
    )