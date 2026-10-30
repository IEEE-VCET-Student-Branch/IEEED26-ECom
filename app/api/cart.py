from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from ..database import get_db
from ..dependencies import validate_customer_id
from ..models import Cart, CartItem, Product
from ..schemas import CartItemIn, CartOut
router = APIRouter(prefix="/cart", tags=["cart"])


def get_or_create(db: Session, customer_id: str) -> Cart:
    customer_id = customer_id.strip()
    cart = db.query(Cart).filter(Cart.customer_id == customer_id).first()
    if not cart:
        cart = Cart(customer_id=customer_id)
        db.add(cart)
        try:
            db.commit()
            db.refresh(cart)
        except IntegrityError:
            db.rollback()
            cart = db.query(Cart).filter(Cart.customer_id == customer_id).first()
    return cart


def as_out(cart: Cart) -> CartOut:
    items = [
        dict(
            product_id=i.product_id,
            sku=i.product.sku,
            name=i.product.name,
            quantity=i.quantity,
            unit_price_minor=i.product.price_minor,
            line_total_minor=i.product.price_minor * i.quantity,
        )
        for i in cart.items
    ]
    return CartOut(
        customer_id=cart.customer_id,
        items=items,
        subtotal_minor=sum(i["line_total_minor"] for i in items),
    )


@router.get("/{customer_id}", response_model=CartOut)
@router.get("/{customer_id}/", response_model=CartOut, include_in_schema=False)
def get_cart(
    customer_id: str = Depends(validate_customer_id),
    db: Session = Depends(get_db),
):
    return as_out(get_or_create(db, customer_id))


@router.post("/{customer_id}/items", response_model=CartOut)
@router.post("/{customer_id}/items/", response_model=CartOut, include_in_schema=False)
def add_item(
    payload: CartItemIn,
    customer_id: str = Depends(validate_customer_id),
    db: Session = Depends(get_db),
):
    cart = get_or_create(db, customer_id)
    product = db.get(Product, payload.product_id)
    if not product:
        raise HTTPException(404, "Product not found")
    item = next((x for x in cart.items if x.product_id == product.id), None)
    if item:
        item.quantity += payload.quantity
    else:
        cart.items.append(CartItem(product_id=product.id, quantity=payload.quantity))
    db.commit()
    db.refresh(cart)
    return as_out(cart)
