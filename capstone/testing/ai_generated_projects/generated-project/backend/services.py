from sqlalchemy.orm import Session
from fastapi import HTTPException

from models import InventoryItem
from schemas import InventoryItemCreate

class InventoryService:
    @staticmethod
    def add_item(db: Session, item_create: InventoryItemCreate) -> InventoryItem:
        item = InventoryItem(
            name=item_create.name,
            quantity=item_create.quantity,
            price=item_create.price
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        return item

    @staticmethod
    def list_items(db: Session):
        return db.query(InventoryItem).all()

    @staticmethod
    def update_item_quantity(db: Session, item_id: int, quantity: int) -> InventoryItem:
        item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")
        item.quantity = quantity
        db.commit()
        db.refresh(item)
        return item

    @staticmethod
    def delete_item(db: Session, item_id: int):
        item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")
        db.delete(item)
        db.commit()