from fastapi import HTTPException
from sqlalchemy import update
from sqlalchemy.orm import Session
from ..models import CartItem, Product


def validate(items: list[CartItem]) -> None:
    for item in items:
        if item.quantity > item.product.inventory:
            raise HTTPException(409, f"Insufficient inventory for {item.product.sku}")


def available(item: CartItem) -> int:
    return item.product.inventory


def reserve(db: Session, items: list[CartItem]) -> None:
    """Atomically reserve inventory for every cart line.

    The conditional UPDATE is the authority for both validation and
    reservation: it cannot oversell when another checkout commits between a
    previous read and this write. A zero row count means the line no longer
    fits in the available inventory.
    """
    for item in items:
        result = db.execute(
            update(Product)
            .where(Product.id == item.product_id, Product.inventory >= item.quantity)
            .values(inventory=Product.inventory - item.quantity)
        )
        if result.rowcount != 1:
            raise HTTPException(409, f"Insufficient inventory for {item.product.sku}")
