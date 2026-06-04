from fastapi import FastAPI, HTTPException, Depends, Path
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from models import Base, InventoryItem
from schemas import (
    InventoryCreate,
    InventoryResponse,
    InventoryUpdateQuantity
)
from database import engine, get_db
from services import (
    create_inventory_item,
    list_inventory_items,
    update_inventory_quantity,
    delete_inventory_item
)

Base.metadata.create_all(bind=engine)

app = FastAPI()


@app.post("/api/inventory", response_model=InventoryResponse, status_code=201)
def add_inventory(item: InventoryCreate, db: Session = Depends(get_db)):
    db_item = create_inventory_item(db, item)
    return db_item


@app.get("/api/inventory", response_model=List[InventoryResponse])
def get_all_inventory(db: Session = Depends(get_db)):
    return list_inventory_items(db)


@app.patch("/api/inventory/{item_id}", response_model=InventoryResponse)
def patch_inventory(
    item_id: str = Path(..., description="The ID of the inventory item."),
    update: InventoryUpdateQuantity = ...,
    db: Session = Depends(get_db)
):
    updated_item = update_inventory_quantity(db, item_id, update.quantity)
    if updated_item is None:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    return updated_item


@app.delete("/api/inventory/{item_id}", status_code=204)
def delete_inventory(
    item_id: str = Path(..., description="The ID of the inventory item."),
    db: Session = Depends(get_db)
):
    success = delete_inventory_item(db, item_id)
    if not success:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    return