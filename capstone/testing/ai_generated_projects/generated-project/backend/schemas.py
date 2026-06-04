from pydantic import BaseModel, Field

class InventoryItemCreate(BaseModel):
    name: str = Field(..., max_length=255)
    quantity: int = Field(..., ge=0)
    price: float = Field(..., ge=0.0)

class InventoryItemUpdate(BaseModel):
    quantity: int = Field(..., ge=0)

class InventoryItemResponse(BaseModel):
    id: int
    name: str
    quantity: int
    price: float

    class Config:
        orm_mode = True