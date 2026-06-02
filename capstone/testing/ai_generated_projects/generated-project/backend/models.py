from pydantic import BaseModel, Field, conint, confloat
from typing import List


class ItemCreate(BaseModel):
    name: str = Field(..., min_length=1)
    quantity: conint(ge=0)
    price: confloat(ge=0)


class ItemResponse(BaseModel):
    id: str
    name: str
    quantity: int
    price: float


class ItemUpdateQuantity(BaseModel):
    quantity: conint(ge=0)