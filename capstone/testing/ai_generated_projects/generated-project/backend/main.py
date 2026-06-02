from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, PositiveInt, constr, confloat
from typing import Dict, List
import uuid

app = FastAPI(
    title="Inventory Management API",
    description="Simple in-memory inventory API.",
    version="1.0.0"
)

# ======== Models ========

class ItemCreate(BaseModel):
    name: constr(strip_whitespace=True, min_length=1)
    quantity: PositiveInt
    price: confloat(ge=0.0)

class ItemUpdateQuantity(BaseModel):
    quantity: PositiveInt

class ItemResponse(BaseModel):
    id: str
    name: str
    quantity: int
    price: float

# ======== Services ========

class InventoryService:
    def __init__(self):
        # store items by UUID string -> item dict
        self._store: Dict[str, dict] = {}

    def add_item(self, item: ItemCreate) -> dict:
        item_id = str(uuid.uuid4())
        item_obj = {
            "id": item_id,
            "name": item.name,
            "quantity": item.quantity,
            "price": item.price
        }
        self._store[item_id] = item_obj
        return item_obj

    def get_all_items(self) -> List[dict]:
        return list(self._store.values())

    def update_quantity(self, item_id: str, quantity: int) -> dict:
        if item_id not in self._store:
            return None
        self._store[item_id]['quantity'] = quantity
        return self._store[item_id]

    def delete_item(self, item_id: str) -> bool:
        return self._store.pop(item_id, None) is not None

    def get_item(self, item_id: str) -> dict:
        return self._store.get(item_id)

# Singleton service instance
inventory_service = InventoryService()

# ======== Routes ========

@app.post("/items", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
def add_item(item: ItemCreate):
    new_item = inventory_service.add_item(item)
    return new_item

@app.get("/items", response_model=List[ItemResponse])
def get_all_items():
    items = inventory_service.get_all_items()
    return items

@app.patch("/items/{item_id}", response_model=ItemResponse)
def update_item_quantity(item_id: str, body: ItemUpdateQuantity):
    updated = inventory_service.update_quantity(item_id, body.quantity)
    if not updated:
        raise HTTPException(status_code=404, detail="Item not found")
    return updated

@app.delete("/items/{item_id}")
def delete_item(item_id: str):
    deleted = inventory_service.delete_item(item_id)
    if deleted:
        return {"detail": "Item deleted"}
    raise HTTPException(status_code=404, detail="Item not found")