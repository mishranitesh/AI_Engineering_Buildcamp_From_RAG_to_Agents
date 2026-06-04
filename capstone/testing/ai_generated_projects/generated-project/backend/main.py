from fastapi import FastAPI, HTTPException, Path, status, Depends
from pydantic import BaseModel, Field, NonNegativeInt, condecimal
from typing import List
from sqlalchemy import Column, Integer, String, Numeric, create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session

DATABASE_URL = "sqlite:///./inventory.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()

# --- Data Layer (Model & Repository) ---

class InventoryItem(Base):
    __tablename__ = "inventory_items"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(Numeric(10, 2), nullable=False)

Base.metadata.create_all(bind=engine)

class InventoryRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, name: str, quantity: int, price: float) -> InventoryItem:
        item = InventoryItem(name=name, quantity=quantity, price=price)
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def list(self) -> List[InventoryItem]:
        return self.db.query(InventoryItem).all()

    def get(self, item_id: int) -> InventoryItem | None:
        return self.db.query(InventoryItem).filter(InventoryItem.id == item_id).first()

    def update_quantity(self, item_id: int, quantity: int) -> InventoryItem | None:
        item = self.get(item_id)
        if not item:
            return None
        item.quantity = quantity
        self.db.commit()
        self.db.refresh(item)
        return item

    def delete(self, item_id: int) -> bool:
        item = self.get(item_id)
        if not item:
            return False
        self.db.delete(item)
        self.db.commit()
        return True

# --- Application Layer (Schemas & Service) ---

class InventoryCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    quantity: NonNegativeInt
    price: condecimal(gt=0, max_digits=10, decimal_places=2)

class InventoryResponse(BaseModel):
    id: int
    name: str
    quantity: int
    price: condecimal(max_digits=10, decimal_places=2)

    class Config:
        orm_mode = True

class UpdateQuantityRequest(BaseModel):
    quantity: NonNegativeInt

class InventoryService:
    def __init__(self, repo: InventoryRepository):
        self.repo = repo

    def add_item(self, data: InventoryCreateRequest) -> InventoryItem:
        return self.repo.create(
            name=data.name.strip(),
            quantity=data.quantity,
            price=float(data.price),
        )

    def list_items(self) -> List[InventoryItem]:
        return self.repo.list()

    def update_item_quantity(self, item_id: int, quantity: int) -> InventoryItem:
        if quantity < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Quantity must be 0 or greater."
            )
        item = self.repo.update_quantity(item_id, quantity)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Inventory item not found."
            )
        return item

    def delete_item(self, item_id: int):
        deleted = self.repo.delete(item_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Inventory item not found."
            )

# --- Dependency ---

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_service(db: Session = Depends(get_db)) -> InventoryService:
    return InventoryService(InventoryRepository(db))

# --- Presentation Layer (API) ---

app = FastAPI()

@app.post(
    "/inventory",
    response_model=InventoryResponse,
    status_code=status.HTTP_201_CREATED,
    responses={400: {"description": "Bad Request", "content": {"application/json": {}}}}
)
def add_inventory_item(
    item: InventoryCreateRequest,
    svc: InventoryService = Depends(get_service)
):
    try:
        created = svc.add_item(item)
        return created
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid inventory item data."
        )

@app.get(
    "/inventory",
    response_model=List[InventoryResponse],
    status_code=status.HTTP_200_OK
)
def list_inventory_items(
    svc: InventoryService = Depends(get_service)
):
    return svc.list_items()

@app.put(
    "/inventory/{item_id}/quantity",
    response_model=InventoryResponse,
    responses={
        400: {"description": "Bad Request", "content": {"application/json": {}}},
        404: {"description": "Not Found", "content": {"application/json": {}}}
    }
)
def update_inventory_quantity(
    item_id: int = Path(..., gt=0),
    body: UpdateQuantityRequest = ...,
    svc: InventoryService = Depends(get_service)
):
    return svc.update_item_quantity(item_id, body.quantity)

@app.delete(
    "/inventory/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        204: {"description": "No Content"},
        404: {"description": "Not Found", "content": {"application/json": {}}}
    }
)
def delete_inventory_item(
    item_id: int = Path(..., gt=0),
    svc: InventoryService = Depends(get_service)
):
    svc.delete_item(item_id)
    return None