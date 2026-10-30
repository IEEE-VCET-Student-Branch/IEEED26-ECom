from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Cart, CartItem, Product
from ..schemas import CartItemIn, CartOut
from ..services.pricing import calculate
router = APIRouter(prefix="/cart", tags=["cart"])


def get_or_create(db: Session, customer_id: str) -> Cart:
    cart = db.query(Cart).filter(Cart.customer_id == customer_id).first()
    if cart:
        return cart
    cart = Cart(customer_id=customer_id)
    db.add(cart)
    try:
        db.commit()
    except IntegrityError:
        # A concurrent request created the cart between the lookup and this
        # insert. Roll back and reuse the row it committed.
        db.rollback()
        return db.query(Cart).filter(Cart.customer_id == customer_id).one()
    return cart


def as_out(cart: Cart) -> CartOut:
    items = [dict(product_id=i.product_id, sku=i.product.sku, name=i.product.name,
                  quantity=i.quantity, unit_price_minor=i.product.price_minor,
                  line_total_minor=i.product.price_minor * i.quantity) for i in cart.items]
    return CartOut(customer_id=cart.customer_id, items=items,
                   subtotal_minor=sum(i["line_total_minor"] for i in items))


@router.get("/{customer_id}", response_model=CartOut)
def get_cart(customer_id: str, db: Session = Depends(get_db)):
    return as_out(get_or_create(db, customer_id))


@router.post("/{customer_id}/items", response_model=CartOut)
def add_item(customer_id: str, payload: CartItemIn, db: Session = Depends(get_db)):
    cart = get_or_create(db, customer_id)
    product = db.get(Product, payload.product_id)
    if not product:
        raise HTTPException(404, "Product not found")
    item = next((x for x in cart.items if x.product_id == product.id), None)
    if item is not None:
        # Increment in SQL so concurrent adds cannot overwrite each other's
        # read-modify-write of the same line.
        db.execute(
            update(CartItem)
            .where(CartItem.id == item.id)
            .values(quantity=CartItem.quantity + payload.quantity)
        )
        db.commit()
    else:
        db.add(CartItem(cart_id=cart.id, product_id=product.id, quantity=payload.quantity))
        try:
            db.commit()
        except IntegrityError:
            # A concurrent request inserted the same line first; add to it
            # instead of creating a duplicate.
            db.rollback()
            db.execute(
                update(CartItem)
                .where(CartItem.cart_id == cart.id, CartItem.product_id == product.id)
                .values(quantity=CartItem.quantity + payload.quantity)
            )
            db.commit()
    db.refresh(cart)
    return as_out(cart)
