from pydantic import BaseModel, Field, PositiveInt, condecimal, constr
from typing import Optional


class InventoryItemBase(BaseModel):
    name: constr(min_length=1)
    quantity: int = Field(..., ge=0, description="Quantity must be >= 0")
    price: condecimal(ge=0, decimal_places=2) = Field(..., description="Price must be >= 0.00")

    class Config:
        orm_mode = True


class InventoryItemCreate(InventoryItemBase):
    pass


class InventoryItemResponse(InventoryItemBase):
    id: int


class InventoryItemUpdateQuantity(BaseModel):
    quantity: int = Field(..., ge=0, description="Quantity must be >= 0")