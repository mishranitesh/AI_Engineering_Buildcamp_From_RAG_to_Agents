from fastapi import FastAPI, HTTPException, Depends, APIRouter
from sqlalchemy import Column, Integer, String, Float, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from pydantic import BaseModel, conint, constr, confloat
from typing import List, Optional
import uvicorn

DATABASE_URL = "sqlite:///./inventory.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# ========== MODELS ==========

class InventoryItem(Base):
    __tablename__ = "inventory_items"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)

Base.metadata.create_all(bind=engine)

# ========== SCHEMAS ==========

class InventoryCreate(BaseModel):
    name: constr(min_length=1, max_length=100)
    quantity: conint(ge=0)
    price: confloat(ge=0.0)

class InventoryUpdate(BaseModel):
    quantity: conint(ge=0)

class InventoryResponse(BaseModel):
    id: int
    name: str
    quantity: int
    price: float

    class Config:
        orm_mode = True

# ========== SERVICES ==========

class InventoryService:
    def __init__(self, db: Session):
        self.db = db

    def create_item(self, item_data: InventoryCreate) -> InventoryItem:
        item = InventoryItem(
            name=item_data.name.strip(),
            quantity=item_data.quantity,
            price=item_data.price
        )
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def get_all_items(self) -> List[InventoryItem]:
        return self.db.query(InventoryItem).all()

    def update_item_quantity(self, item_id: int, quantity: int) -> InventoryItem:
        item = self.db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")
        item.quantity = quantity
        self.db.commit()
        self.db.refresh(item)
        return item

    def delete_item(self, item_id: int) -> None:
        item = self.db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")
        self.db.delete(item)
        self.db.commit()

# ========== DEPENDENCIES ==========

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_inventory_service(db: Session = Depends(get_db)):
    return InventoryService(db)

# ========== ROUTES ==========

router = APIRouter(prefix="/api/inventory", tags=["inventory"])

@router.post(
    "", 
    response_model=InventoryResponse, 
    status_code=201,
    summary="Create an inventory item"
)
def create_inventory_item(
    item: InventoryCreate,
    service: InventoryService = Depends(get_inventory_service)
):
    return service.create_item(item)

@router.get(
    "", 
    response_model=List[InventoryResponse],
    summary="Get all inventory items"
)
def list_inventory_items(
    service: InventoryService = Depends(get_inventory_service)
):
    return service.get_all_items()

@router.patch(
    "/{item_id}", 
    response_model=InventoryResponse,
    summary="Update quantity of an inventory item"
)
def update_inventory_item_quantity(
    item_id: int,
    update: InventoryUpdate,
    service: InventoryService = Depends(get_inventory_service)
):
    return service.update_item_quantity(item_id, update.quantity)

@router.delete(
    "/{item_id}",
    status_code=204,
    summary="Delete an inventory item"
)
def delete_inventory_item(
    item_id: int,
    service: InventoryService = Depends(get_inventory_service)
):
    service.delete_item(item_id)
    return None

# ========== APP SETUP ==========

app = FastAPI(
    title="Inventory Management API",
    description="CRUD inventory management system.",
    version="1.0.0"
)

app.include_router(router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)