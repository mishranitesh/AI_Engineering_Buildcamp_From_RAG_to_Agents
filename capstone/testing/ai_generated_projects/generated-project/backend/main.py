from fastapi import FastAPI, HTTPException, status, Path
from fastapi.responses import JSONResponse
from typing import List, Dict
from uuid import uuid4, UUID
from pydantic import BaseModel, Field, constr, conint, confloat, validator

app = FastAPI(title="Inventory API")

# In-memory storage (id -> InventoryItem)
inventory_items: Dict[UUID, "InventoryItem"] = {}

# Lowercase name -> id mapping for fast uniqueness check
name_index: Dict[str, UUID] = {}


class InventoryItemCreate(BaseModel):
    name: constr(strip_whitespace=True, min_length=1)
    quantity: conint(ge=0)
    price: confloat(ge=0)

    @validator("name")
    def name_cannot_be_whitespace(cls, v):
        if not v or not v.strip():
            raise ValueError("Name is required.")
        return v


class InventoryItemOut(BaseModel):
    id: UUID
    name: str
    quantity: int
    price: float


class UpdateQuantityRequest(BaseModel):
    quantity: conint(ge=0)

    @validator("quantity")
    def quantity_is_non_negative(cls, v):
        if v < 0:
            raise ValueError("Quantity must be a non-negative integer.")
        return v


class InventoryService:
    @staticmethod
    def add_item(item: InventoryItemCreate) -> InventoryItemOut:
        lower_name = item.name.strip().lower()
        if lower_name in name_index:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Name must be unique (case-insensitive).",
            )
        item_id = uuid4()
        item_obj = InventoryItemOut(
            id=item_id,
            name=item.name.strip(),
            quantity=item.quantity,
            price=float(item.price),
        )
        inventory_items[item_id] = item_obj
        name_index[lower_name] = item_id
        return item_obj

    @staticmethod
    def list_items() -> List[InventoryItemOut]:
        return list(inventory_items.values())

    @staticmethod
    def get_item_by_id(item_id: UUID) -> InventoryItemOut:
        item = inventory_items.get(item_id)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Item not found.",
            )
        return item

    @staticmethod
    def update_quantity(item_id: UUID, new_quantity: int) -> InventoryItemOut:
        item = InventoryService.get_item_by_id(item_id)
        if new_quantity < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Quantity must be a non-negative integer.",
            )
        updated_item = InventoryItemOut(
            id=item.id,
            name=item.name,
            quantity=new_quantity,
            price=item.price,
        )
        inventory_items[item_id] = updated_item
        return updated_item

    @staticmethod
    def delete_item(item_id: UUID):
        item = InventoryService.get_item_by_id(item_id)
        # Remove from both storages
        lower_name = item.name.lower()
        del inventory_items[item_id]
        if lower_name in name_index:
            del name_index[lower_name]
        return


@app.post("/items", response_model=InventoryItemOut, status_code=status.HTTP_201_CREATED)
def create_inventory_item(item: InventoryItemCreate):
    created_item = InventoryService.add_item(item)
    return created_item


@app.get("/items", response_model=List[InventoryItemOut])
def list_inventory_items():
    return InventoryService.list_items()


@app.patch(
    "/items/{item_id}/quantity",
    response_model=InventoryItemOut,
)
def update_inventory_item_quantity(
    item_id: UUID = Path(..., description="The item's unique identifier"),
    req: UpdateQuantityRequest = ...,
):
    updated_item = InventoryService.update_quantity(item_id, req.quantity)
    return updated_item


@app.delete(
    "/items/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        404: {"model": BaseModel, "content": {"application/json": {"example": {"detail": "Item not found."}}}}
    },
)
def delete_inventory_item(item_id: UUID = Path(..., description="The item's unique identifier")):
    InventoryService.delete_item(item_id)
    return JSONResponse(status_code=status.HTTP_204_NO_CONTENT)