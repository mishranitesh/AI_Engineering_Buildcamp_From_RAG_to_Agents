from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
from typing import Dict, List
from threading import Lock

app = FastAPI(title="Inventory API")

class InventoryItemCreate(BaseModel):
    name: str = Field(..., min_length=1)
    quantity: int = Field(..., ge=0)
    price: float = Field(..., ge=0.0)

    @validator("name")
    def name_cannot_be_blank(cls, v):
        if not v.strip():
            raise ValueError("Name must not be empty")
        return v.strip()

class InventoryItem(InventoryItemCreate):
    id: int

class InventoryQuantityUpdate(BaseModel):
    quantity: int = Field(..., ge=0)

# In-memory store and id lock/incrementor
inventory_store: Dict[int, InventoryItem] = {}
id_lock = Lock()
next_id = 1

def _get_next_id() -> int:
    global next_id
    with id_lock:
        curr = next_id
        next_id += 1
    return curr

# Service Layer
def add_inventory_item(data: InventoryItemCreate) -> InventoryItem:
    item_id = _get_next_id()
    item = InventoryItem(id=item_id, **data.dict())
    inventory_store[item_id] = item
    return item

def get_all_inventory_items() -> List[InventoryItem]:
    return list(inventory_store.values())

def update_inventory_item_quantity(item_id: int, quantity: int) -> InventoryItem:
    if item_id not in inventory_store:
        raise HTTPException(status_code=404, detail="Item not found")
    item = inventory_store[item_id]
    updated_item = InventoryItem(**item.dict(), quantity=quantity)
    inventory_store[item_id] = updated_item
    return updated_item

def delete_inventory_item(item_id: int):
    if item_id not in inventory_store:
        raise HTTPException(status_code=404, detail="Item not found")
    del inventory_store[item_id]

# API Routes
@app.post("/items/", response_model=InventoryItem, status_code=status.HTTP_201_CREATED)
def create_item(item_data: InventoryItemCreate):
    item = add_inventory_item(item_data)
    return item

@app.get("/items/", response_model=List[InventoryItem])
def list_items():
    return get_all_inventory_items()

@app.put("/items/{item_id}/quantity/", response_model=InventoryItem)
def update_item_quantity(item_id: int, quantity_update: InventoryQuantityUpdate):
    updated = update_inventory_item_quantity(item_id, quantity_update.quantity)
    return updated

@app.delete("/items/{item_id}/", response_class=JSONResponse)
def delete_item(item_id: int):
    delete_inventory_item(item_id)
    return {"message": "Item deleted successfully"}