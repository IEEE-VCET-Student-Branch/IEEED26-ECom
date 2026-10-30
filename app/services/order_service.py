from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from ..models import Cart, Order, OrderItem, PaymentAttempt
from ..schemas import CheckoutIn
from ..utils.idempotency import find_order, normalize_key
from . import inventory, payment, pricing


def _is_idempotency_key_conflict(error: IntegrityError) -> bool:
    original = error.orig
    constraint_name = getattr(getattr(original, "diag", None), "constraint_name", None)
    idempotency_indexes = [
        index for index in Order.__table__.indexes
        if index.unique and [column.name for column in index.columns] == ["idempotency_key"]
    ]
    if len(idempotency_indexes) != 1:
        return False
    idempotency_index = idempotency_indexes[0]
    if constraint_name is not None:
        return constraint_name == idempotency_index.name

    # SQLite reports the affected columns instead of a constraint/index name.
    message = str(original).lower()
    return "unique constraint failed: orders.idempotency_key" in message


def create_order(db: Session, request: CheckoutIn, key: str) -> Order:
    key = normalize_key(key)
    try:
        # SQLite's deferred transactions can otherwise fail while upgrading a
        # read snapshot to a writer. Acquire its write reservation before the
        # checkout reads; PostgreSQL relies on the conditional UPDATE below.
        if not db.in_transaction() and db.get_bind().dialect.name == "sqlite":
            db.connection().execute(text("BEGIN IMMEDIATE"))

        existing = find_order(db, key)
        if existing:
            return existing
        cart = db.query(Cart).filter(Cart.customer_id == request.customer_id).first()
        if not cart or not cart.items:
            raise HTTPException(400, "Cart is empty")
        inventory.validate(cart.items)
        quote = pricing.calculate(cart.items, request.discount_code)
        # This provider is deterministic and offline. A real provider must
        # receive the same provider-side idempotency key before charging.
        result = payment.charge(request.payment_token, quote.total_minor)
        if result.status == "declined":
            raise HTTPException(402, "Payment was declined")
        order = Order(customer_id=request.customer_id, status=result.status,
                      subtotal_minor=quote.subtotal_minor, discount_minor=quote.discount_minor,
                      total_minor=quote.total_minor, idempotency_key=key)
        db.add(order)
        try:
            db.flush()
        except IntegrityError as exc:
            if not _is_idempotency_key_conflict(exc):
                raise
            db.rollback()
            existing = find_order(db, key)
            if existing:
                return existing
            raise
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
    except Exception:
        db.rollback()
        raise
