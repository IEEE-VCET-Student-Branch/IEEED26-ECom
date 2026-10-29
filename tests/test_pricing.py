from app.services.pricing import calculate


def test_welcome_discount(seeded):
    seeded.post("/cart/alex/items", json={"product_id": 1, "quantity": 2})
    from app.database import SessionLocal
    from app.models import Cart
    cart = SessionLocal().query(Cart).filter_by(customer_id="alex").first()
    quote = calculate(cart.items, "WELCOME10")
    assert quote.discount_minor == 259
    assert quote.total_minor == 2339


def test_unknown_discount_is_ignored(seeded):
    seeded.post("/cart/alex/items", json={"product_id": 1, "quantity": 1})
    from app.database import SessionLocal
    from app.models import Cart
    cart = SessionLocal().query(Cart).filter_by(customer_id="alex").first()
    assert calculate(cart.items, "OTHER").discount_minor == 0
