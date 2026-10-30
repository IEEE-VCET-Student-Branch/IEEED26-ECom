from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
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

    # Claim the logical key with an uncommitted insert before any payment or
    # inventory work. SQLite serializes writers, so a concurrent request with
    # the same key blocks on this INSERT until the winner commits or rolls
    # back. The unique index then makes the loser replay the winner's order
    # instead of charging and reserving a second time. A rolled-back claim
    # (decline, validation failure, provider error) frees the key for reuse.
    order = Order(
        customer_id=request.customer_id,
        status="pending",
        subtotal_minor=0,
        discount_minor=0,
        total_minor=0,
        idempotency_key=normalized_key,
    )
    db.add(order)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        existing = find_order(db, normalized_key)
        if existing:
            return existing
        raise

    try:
        cart = db.query(Cart).filter(Cart.customer_id == request.customer_id).first()
        if not cart or not cart.items:
            raise HTTPException(400, "Cart is empty")

        inventory.reserve(db, cart.items)
        quote = pricing.calculate(cart.items, request.discount_code)
        result = payment.charge(request.payment_token, quote.total_minor)
        if result.status == "declined":
            raise HTTPException(402, "Payment was declined")

        order.status = result.status
        order.subtotal_minor = quote.subtotal_minor
        order.discount_minor = quote.discount_minor
        order.total_minor = quote.total_minor
        for item in cart.items:
            order.items.append(OrderItem(product_id=item.product_id, sku=item.product.sku,
                                         name=item.product.name, unit_price_minor=item.product.price_minor,
                                         quantity=item.quantity))
        order.payment_attempts.append(PaymentAttempt(status=result.status, provider_reference=result.reference))
        cart.items.clear()
        db.commit()
    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        # The commit may have failed after a concurrent request with the same
        # key won the race. If its order is now visible, return that order.
        existing = find_order(db, normalized_key)
        if existing:
            return existing
        raise

    db.refresh(order)
    return order
