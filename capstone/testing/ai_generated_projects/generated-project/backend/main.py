from fastapi import FastAPI, HTTPException, status, Depends
from typing import List
from sqlalchemy.orm import Session
from models import InventoryItem
from schemas import (
    InventoryItemCreate,
    InventoryItemUpdateQuantity,
    InventoryItemResponse,
)
from services import (
    create_inventory_item,
    get_all_inventory_items,
    update_inventory_item_quantity,
    delete_inventory_item,
)
from database import SessionLocal, engine, Base

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Inventory Management API")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post(
    "/inventory",
    response_model=InventoryItemResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_inventory_item(
    item: InventoryItemCreate, db: Session = Depends(get_db)
):
    return create_inventory_item(db, item)


@app.get("/inventory", response_model=List[InventoryItemResponse])
def get_inventory_items(db: Session = Depends(get_db)):
    return get_all_inventory_items(db)


@app.patch(
    "/inventory/{item_id}/quantity",
    response_model=InventoryItemResponse,
)
def patch_inventory_quantity(
    item_id: int, update: InventoryItemUpdateQuantity, db: Session = Depends(get_db)
):
    return update_inventory_item_quantity(db, item_id, update.quantity)


@app.delete("/inventory/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_inventory(item_id: int, db: Session = Depends(get_db)):
    delete_inventory_item(db, item_id)
    return None