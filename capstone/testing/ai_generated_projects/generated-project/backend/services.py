from sqlalchemy.orm import Session
from models import InventoryItem
from schemas import InventoryCreate
from typing import List, Optional
from datetime import datetime


def create_inventory_item(db: Session, item: InventoryCreate) -> InventoryItem:
    db_item = InventoryItem(
        name=item.name,
        quantity=item.quantity,
        price=item.price,
        created_at=datetime.utcnow()
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


def list_inventory_items(db: Session) -> List[InventoryItem]:
    return db.query(InventoryItem).all()


def update_inventory_quantity(db: Session, item_id: str, quantity: int) -> Optional[InventoryItem]:
    db_item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
    if not db_item:
        return None
    db_item.quantity = quantity
    db.commit()
    db.refresh(db_item)
    return db_item


def delete_inventory_item(db: Session, item_id: str) -> bool:
    db_item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
    if not db_item:
        return False
    db.delete(db_item)
    db.commit()
    return True