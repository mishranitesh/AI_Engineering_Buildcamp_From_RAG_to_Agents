from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session

from models import Base, InventoryItem
from schemas import InventoryItemCreate, InventoryItemResponse, InventoryItemUpdate
from database import SessionLocal, engine
from services import InventoryService

Base.metadata.create_all(bind=engine)

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/inventory", response_model=InventoryItemResponse, status_code=201)
def add_inventory_item(item: InventoryItemCreate, db: Session = Depends(get_db)):
    return InventoryService.add_item(db, item)

@app.get("/inventory", response_model=list[InventoryItemResponse])
def list_inventory_items(db: Session = Depends(get_db)):
    return InventoryService.list_items(db)

@app.patch("/inventory/{item_id}", response_model=InventoryItemResponse)
def update_inventory_item_quantity(item_id: int, update: InventoryItemUpdate, db: Session = Depends(get_db)):
    return InventoryService.update_item_quantity(db, item_id, update.quantity)

@app.delete("/inventory/{item_id}", status_code=204)
def delete_inventory_item(item_id: int, db: Session = Depends(get_db)):
    InventoryService.delete_item(db, item_id)
    return