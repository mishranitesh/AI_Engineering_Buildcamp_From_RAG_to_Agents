from fastapi import FastAPI, HTTPException
from typing import List

from models import ItemCreate, ItemResponse, ItemUpdateQuantity
import services

app = FastAPI(title="Inventory Management API")


@app.post("/items", response_model=ItemResponse, status_code=201)
def create_item(item: ItemCreate):
    new_item = services.add_item(item)
    return new_item


@app.get("/items", response_model=List[ItemResponse])
def get_all_items():
    return services.list_items()


@app.patch("/items/{item_id}", response_model=ItemResponse)
def patch_item_quantity(item_id: str, body: ItemUpdateQuantity):
    updated_item = services.update_item_quantity(item_id, body.quantity)
    if updated_item:
        return updated_item
    raise HTTPException(status_code=404, detail="Item not found")


@app.delete("/items/{item_id}")
def delete_item(item_id: str):
    was_deleted = services.delete_item(item_id)
    if was_deleted:
        return {"detail": "Item deleted"}
    raise HTTPException(status_code=404, detail="Item not found")