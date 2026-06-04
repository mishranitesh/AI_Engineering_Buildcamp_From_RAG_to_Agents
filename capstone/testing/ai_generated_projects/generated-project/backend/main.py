from fastapi import FastAPI, HTTPException, status, Path
from fastapi.responses import JSONResponse
from pydantic import BaseModel, constr, PositiveInt, NonNegativeInt, condecimal
from typing import List
from uuid import uuid4, UUID
from sqlalchemy import create_engine, Column, String, Integer, Numeric
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, scoped_session

# SQLAlchemy setup (using SQLite for demonstration, replace with real DB in prod)
DATABASE_URL = "sqlite:///./inventory.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))
Base = declarative_base()

# --- Models ---

class InventoryItemDB(Base):
    __tablename__ = "inventory_items"
    id = Column(String(36), primary_key=True, index=True)
    name = Column(String(128), nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(Numeric(10, 2), nullable=False)

# --- Pydantic Schemas ---

class InventoryItemCreate(BaseModel):
    name: constr(strip_whitespace=True, min_length=1, max_length=128)
    quantity: NonNegativeInt
    price: condecimal(gt=0, max_digits=10, decimal_places=2)

class InventoryItemResponse(BaseModel):
    id: str
    name: str
    quantity: int
    price: float

    class Config:
        orm_mode = True

class InventoryItemQuantityUpdate(BaseModel):
    quantity: NonNegativeInt

# --- Service Layer ---

class InventoryService:
    @staticmethod
    def create_item(db: Session, data: InventoryItemCreate) -> InventoryItemDB:
        item = InventoryItemDB(
            id=str(uuid4()),
            name=data.name,
            quantity=data.quantity,
            price=data.price
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        return item

    @staticmethod
    def get_items(db: Session) -> List[InventoryItemDB]:
        return db.query(InventoryItemDB).all()

    @staticmethod
    def update_quantity(db: Session, item_id: str, quantity: int) -> InventoryItemDB:
        item = db.query(InventoryItemDB).filter(InventoryItemDB.id == item_id).first()
        if not item:
            raise HTTPException(status_code=404, detail="Inventory item not found")
        item.quantity = quantity
        db.commit()
        db.refresh(item)
        return item

    @staticmethod
    def delete_item(db: Session, item_id: str):
        item = db.query(InventoryItemDB).filter(InventoryItemDB.id == item_id).first()
        if not item:
            raise HTTPException(status_code=404, detail="Inventory item not found")
        db.delete(item)
        db.commit()

# --- FastAPI App & Routes ---

app = FastAPI(title="Inventory Management API", version="1.0.0")

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/api/inventory", response_model=InventoryItemResponse, status_code=status.HTTP_201_CREATED)
def add_inventory_item(item: InventoryItemCreate, db: Session = next(get_db())):
    result = InventoryService.create_item(db, item)
    return InventoryItemResponse.from_orm(result)

@app.get("/api/inventory", response_model=List[InventoryItemResponse])
def list_inventory_items(db: Session = next(get_db())):
    items = InventoryService.get_items(db)
    return [InventoryItemResponse.from_orm(i) for i in items]

@app.put("/api/inventory/{item_id}/quantity", response_model=InventoryItemResponse)
def update_inventory_quantity(
    item_id: str = Path(..., title="Inventory Item ID"),
    update: InventoryItemQuantityUpdate = ...,
    db: Session = next(get_db())
):
    result = InventoryService.update_quantity(db, item_id, update.quantity)
    return InventoryItemResponse.from_orm(result)

@app.delete("/api/inventory/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_inventory_item(item_id: str = Path(..., title="Inventory Item ID"), db: Session = next(get_db())):
    InventoryService.delete_item(db, item_id)
    return JSONResponse(status_code=status.HTTP_204_NO_CONTENT, content=None)