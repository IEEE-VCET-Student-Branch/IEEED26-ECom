from fastapi import HTTPException
from sqlalchemy.orm import Session
from ..models import CartItem


def validate(items: list[CartItem]) -> None:
    for item in items:
        if item.quantity > item.product.inventory:
            raise HTTPException(409, f"Insufficient inventory for {item.product.sku}")


def available(item: CartItem) -> int:
    return item.product.inventory


def reserve(db: Session, items: list[CartItem]) -> None:
    for item in items:
        db.refresh(item.product)
    validate(items)
    for item in items:
        item.product.inventory -= item.quantity
    db.flush()
