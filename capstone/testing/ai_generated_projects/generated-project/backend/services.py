from typing import List
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, NoResultFound
from fastapi import HTTPException, status
from models import InventoryItem
from schemas import InventoryItemCreate

from database import SessionLocal


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_inventory_item(db: Session, item: InventoryItemCreate) -> InventoryItem:
    db_item = InventoryItem(**item.dict())
    db.add(db_item)
    try:
        db.commit()
        db.refresh(db_item)
        return db_item
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Item with that name already exists.",
        )


def get_all_inventory_items(db: Session) -> List[InventoryItem]:
    return db.query(InventoryItem).all()


def update_inventory_item_quantity(db: Session, item_id: str, quantity: int) -> InventoryItem:
    item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    item.quantity = quantity
    db.commit()
    db.refresh(item)
    return item


def delete_inventory_item(db: Session, item_id: str):
    item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    db.delete(item)
    db.commit()