import pytest
from fastapi.testclient import TestClient
from main import app
import sys

client = TestClient(app)

def test_create_inventory_item():
    response = client.post(
        "/inventory",
        json={"name": "Widget", "quantity": 10, "price": "5.99"}
    )
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["id"] > 0
    assert data["name"] == "Widget"
    assert data["quantity"] == 10
    assert data["price"] == "5.99"

def test_very_large_quantity():
    # Python ints are unbounded but SQLite's INTEGER is up to 9223372036854775807 (signed 64-bit)
    max_sqlite_int = 9223372036854775807
    response = client.post(
        "/inventory",
        json={"name": "BigStock", "quantity": max_sqlite_int, "price": "99.99"}
    )
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["quantity"] == max_sqlite_int
    assert data["name"] == "BigStock"

def test_negative_quantity_fails():
    response = client.post(
        "/inventory",
        json={"name": "InvalidWidget", "quantity": -1, "price": "3.50"}
    )
    assert response.status_code == 422  # validation error

def test_invalid_price_fails():
    response = client.post(
        "/inventory",
        json={"name": "CheapWidget", "quantity": 1, "price": "-0.01"}
    )
    assert response.status_code == 422  # validation error