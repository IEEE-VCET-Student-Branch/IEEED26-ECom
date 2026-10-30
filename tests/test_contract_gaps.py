from app.database import SessionLocal
from app.models import Order, PaymentAttempt, Product


def add_item(client, customer_id, product_id, quantity):
    return client.post(
        f"/cart/{customer_id}/items",
        json={"product_id": product_id, "quantity": quantity},
    )


def checkout(client, customer_id, key, discount_code=None):
    body = {"customer_id": customer_id, "payment_token": "tok"}
    if discount_code is not None:
        body["discount_code"] = discount_code
    return client.post("/checkout", headers={"Idempotency-Key": key}, json=body)


def test_product_listing_is_ordered_by_id(seeded):
    response = seeded.get("/products", follow_redirects=False)
    assert response.status_code == 200
    ids = [product["id"] for product in response.json()]
    assert ids == sorted(ids)


def test_adding_a_missing_product_returns_404_without_changing_the_cart(seeded):
    response = add_item(seeded, "alex", 999, 1)

    assert response.status_code == 404
    assert seeded.get("/cart/alex").json()["items"] == []


def test_cart_activity_never_reserves_inventory(seeded):
    add_item(seeded, "alex", 1, 5)
    assert seeded.get("/cart/alex").json()["items"][0]["quantity"] == 5
    assert seeded.get("/products/1").json()["inventory"] == 20


def test_cart_quantity_boundaries(seeded):
    assert add_item(seeded, "alex", 1, 99).status_code == 200
    assert add_item(seeded, "alex", 1, 0).status_code == 422
    assert add_item(seeded, "alex", 1, 100).status_code == 422


def test_order_listing_is_ordered_by_id_and_contains_paid_orders(seeded):
    add_item(seeded, "alex", 1, 1)
    assert checkout(seeded, "alex", "gap-order-1").status_code == 200

    add_item(seeded, "bob", 2, 1)
    assert checkout(seeded, "bob", "gap-order-2").status_code == 200

    orders = seeded.get("/orders").json()
    assert [order["id"] for order in orders] == sorted(order["id"] for order in orders)
    assert {order["status"] for order in orders} == {"paid"}


def test_checkout_discount_is_case_insensitive(seeded):
    add_item(seeded, "alex", 1, 2)
    response = checkout(seeded, "alex", "gap-discount-1", discount_code="welcome10")

    assert response.status_code == 200
    assert response.json()["discount_minor"] == 259
    assert response.json()["total_minor"] == 2339


def test_insufficient_inventory_leaves_cart_and_records_no_attempt(seeded):
    add_item(seeded, "alex", 1, 21)

    response = checkout(seeded, "alex", "gap-inventory-1")

    assert response.status_code == 409
    assert seeded.get("/cart/alex").json()["items"][0]["quantity"] == 21
    assert seeded.get("/products/1").json()["inventory"] == 20
    db = SessionLocal()
    try:
        assert db.query(Order).count() == 0
        assert db.query(PaymentAttempt).count() == 0
        assert db.get(Product, 1).inventory == 20
    finally:
        db.close()
