import uuid
from typing import Dict, List, Optional
from models import ItemCreate, ItemResponse

# In-memory store: {item_id: ItemResponse}
_inventory_store: Dict[str, ItemResponse] = {}


def add_item(item_data: ItemCreate) -> ItemResponse:
    item_id = str(uuid.uuid4())
    new_item = ItemResponse(
        id=item_id,
        name=item_data.name,
        quantity=item_data.quantity,
        price=item_data.price
    )
    _inventory_store[item_id] = new_item
    return new_item


def list_items() -> List[ItemResponse]:
    return list(_inventory_store.values())


def update_item_quantity(item_id: str, new_quantity: int) -> Optional[ItemResponse]:
    if item_id in _inventory_store:
        item = _inventory_store[item_id]
        updated_item = ItemResponse(
            id=item.id,
            name=item.name,
            quantity=new_quantity,
            price=item.price
        )
        _inventory_store[item_id] = updated_item
        return updated_item
    return None


def delete_item(item_id: str) -> bool:
    if item_id in _inventory_store:
        del _inventory_store[item_id]
        return True
    return False