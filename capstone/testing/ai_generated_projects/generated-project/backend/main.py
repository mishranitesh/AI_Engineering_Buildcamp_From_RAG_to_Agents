from fastapi import FastAPI, Depends, HTTPException, status, Path
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import List
import uvicorn

from models import Base, InventoryItem
from schemas import InventoryItemCreate, InventoryItemOut, InventoryItemUpdateQuantity
from services import (
    get_db,
    create_inventory_item,
    get_all_inventory_items,
    update_inventory_item_quantity,
    delete_inventory_item,
)
from auth import get_current_user, User

app = FastAPI()


@app.post(
    "/api/inventory",
    response_model=InventoryItemOut,
    status_code=status.HTTP_201_CREATED,
)
def api_create_inventory_item(
    item: InventoryItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return create_inventory_item(db, item)


@app.get(
    "/api/inventory",
    response_model=List[InventoryItemOut],
)
def api_get_all_inventory_items(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_all_inventory_items(db)


@app.patch(
    "/api/inventory/{item_id}/quantity",
    response_model=InventoryItemOut,
)
def api_update_inventory_quantity(
    item_id: str = Path(..., title="The ID of the item to update"),
    patch: InventoryItemUpdateQuantity = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return update_inventory_item_quantity(db, item_id, patch.quantity)


@app.delete(
    "/api/inventory/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def api_delete_inventory_item(
    item_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    delete_inventory_item(db, item_id)
    return


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000)