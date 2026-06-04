from pydantic import BaseModel, Field
from typing import Optional


class InventoryItemBase(BaseModel):
    name: str = Field(..., example="Widget")
    quantity: int = Field(..., example=100, ge=0)
    price: float = Field(..., example=19.99, ge=0)


class InventoryItemCreate(InventoryItemBase):
    pass


class InventoryItemOut(InventoryItemBase):
    id: str

    class Config:
        orm_mode = True


class InventoryItemUpdateQuantity(BaseModel):
    quantity: int = Field(..., example=200, ge=0)