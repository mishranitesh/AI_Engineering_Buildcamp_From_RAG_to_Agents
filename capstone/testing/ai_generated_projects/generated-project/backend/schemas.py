from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class InventoryCreate(BaseModel):
    name: str = Field(..., min_length=1)
    quantity: int = Field(..., ge=0)
    price: float = Field(..., ge=0.0)


class InventoryUpdateQuantity(BaseModel):
    quantity: int = Field(..., ge=0)


class InventoryResponse(BaseModel):
    id: str
    name: str
    quantity: int
    price: float
    created_at: datetime

    class Config:
        orm_mode = True