from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from models import InventoryItem
from schemas import InventoryItemCreate


def create_inventory_item(db: Session, item_in: InventoryItemCreate) -> InventoryItem:
    item = InventoryItem(
        name=item_in.name.strip(),
        quantity=item_in.quantity,
        price=round(float(item_in.price), 2),
    )
    db.add(item)
    try:
        db.commit()
        db.refresh(item)
        return item
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inventory item could not be created.",
        )


def get_all_inventory_items(db: Session):
    return db.query(InventoryItem).all()


def update_inventory_item_quantity(db: Session, item_id: int, quantity: int):
    item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Inventory item not found."
        )
    if quantity < 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Quantity must be >= 0.",
        )
    item.quantity = quantity
    db.commit()
    db.refresh(item)
    return item


def delete_inventory_item(db: Session, item_id: int):
    item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Inventory item not found."
        )
    db.delete(item)
    db.commit()