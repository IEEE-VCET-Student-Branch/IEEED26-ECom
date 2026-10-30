from fastapi import HTTPException
from sqlalchemy.orm import Session
from ..models import Cart, Order, OrderItem, PaymentAttempt
from ..schemas import CheckoutIn
from ..utils.idempotency import find_order, normalize_key
from . import inventory, payment, pricing


def create_order(db: Session, request: CheckoutIn, key: str) -> Order:
    normalized_key = normalize_key(key)
    existing = find_order(db, normalized_key)
    if existing:
        return existing
    cart = db.query(Cart).filter(Cart.customer_id == request.customer_id).first()
    if not cart or not cart.items:
        raise HTTPException(400, "Cart is empty")
    inventory.validate(cart.items)
    quote = pricing.calculate(cart.items, request.discount_code)
    result = payment.charge(request.payment_token, quote.total_minor)
    if result.status == "declined":
        raise HTTPException(402, "Payment was declined")
    order = Order(customer_id=request.customer_id, status=result.status,
                  subtotal_minor=quote.subtotal_minor, discount_minor=quote.discount_minor,
                  total_minor=quote.total_minor, idempotency_key=normalized_key)
    db.add(order)
    db.flush()
    for item in cart.items:
        order.items.append(OrderItem(product_id=item.product_id, sku=item.product.sku,
                                     name=item.product.name, unit_price_minor=item.product.price_minor,
                                     quantity=item.quantity))
    inventory.reserve(db, cart.items)
    order.payment_attempts.append(PaymentAttempt(status=result.status, provider_reference=result.reference))
    cart.items.clear()
    db.commit()
    db.refresh(order)
    return order
