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
    validate(items)
    for item in sorted(items, key=lambda cart_item: cart_item.product_id):
        result = db.execute(
            update(Product)
            .where(Product.id == item.product_id, Product.inventory >= item.quantity)
            .values(inventory=Product.inventory - item.quantity)
            .execution_options(synchronize_session=False)
        )
        if result.rowcount != 1:
            raise HTTPException(409, f"Insufficient inventory for {item.product.sku}")
