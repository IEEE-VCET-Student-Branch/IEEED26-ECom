import concurrent.futures
import pytest
from app.config import get_settings
from app.database import SessionLocal
from app.models import Cart, CartItem, Order, OrderItem, PaymentAttempt, Product
from app.schemas import CartItemOut, CartOut, OrderItemOut, OrderOut
from app.services.pricing import calculate
from app.utils.idempotency import key_length


def add_item(client, customer_id, product_id, quantity):
    return client.post(
        f"/cart/{customer_id}/items",
        json={"product_id": product_id, "quantity": quantity},
    )


def checkout(client, customer_id, key, payment_token="tok", discount_code=None):
    body = {"customer_id": customer_id, "payment_token": payment_token}
    if discount_code is not None:
        body["discount_code"] = discount_code
    return client.post("/checkout", headers={"Idempotency-Key": key}, json=body)


def test_idempotency_key_casing_retry(seeded):
    """Bug 1: Casing differences in Idempotency-Key header must return identical order."""
    add_item(seeded, "case_user", 1, 1)
    res1 = checkout(seeded, "case_user", "ORDER-KEY-ABC")
    assert res1.status_code == 200
    order1 = res1.json()

    # Retry with lowercase version of same logical key
    res2 = checkout(seeded, "case_user", "order-key-abc")
    assert res2.status_code == 200
    order2 = res2.json()

    assert order1["id"] == order2["id"]
    assert order1 == order2
    # Ensure inventory was only decremented once (20 - 1 = 19)
    assert seeded.get("/products/1").json()["inventory"] == 19


def test_idempotency_key_whitespace_retry(seeded):
    """Bug 1: Surrounding whitespace in Idempotency-Key must resolve to the same logical key."""
    add_item(seeded, "ws_user", 1, 1)
    res1 = checkout(seeded, "ws_user", "   spaced-key-1   ")
    assert res1.status_code == 200
    order1 = res1.json()

    # Retry with trimmed and mixed-case key
    res2 = checkout(seeded, "ws_user", "SPACED-KEY-1")
    assert res2.status_code == 200
    order2 = res2.json()

    assert order1["id"] == order2["id"]
    assert order1 == order2


def test_blank_idempotency_key_rejected(seeded):
    """Bug 2: Whitespace-only or blank Idempotency-Key must be rejected with 400."""
    add_item(seeded, "blank_key_user", 1, 1)
    res = checkout(seeded, "blank_key_user", "   ")
    assert res.status_code == 400

    res_tab = checkout(seeded, "blank_key_user", "\t \n")
    assert res_tab.status_code == 400


def test_custom_payment_decline_token(seeded, monkeypatch):
    """Bug 3: PAYMENT_DECLINE_TOKEN environment setting must be respected."""
    monkeypatch.setenv("PAYMENT_DECLINE_TOKEN", "REJECT_ME")
    get_settings.cache_clear()

    add_item(seeded, "decline_user", 1, 1)

    # Token "decline" should now succeed because decline token is REJECT_ME
    res_decline = checkout(seeded, "decline_user", "k-decline-old", payment_token="decline")
    assert res_decline.status_code == 200

    # Token "REJECT_ME" should be declined with 402
    add_item(seeded, "decline_user2", 1, 1)
    res_reject = checkout(seeded, "decline_user2", "k-custom-decline", payment_token="REJECT_ME")
    assert res_reject.status_code == 402

    get_settings.cache_clear()


def test_products_endpoint_without_trailing_slash(seeded):
    """Bug 4: GET /products must return 200 directly without 307 redirect."""
    res_no_redirect = seeded.get("/products", follow_redirects=False)
    assert res_no_redirect.status_code == 200
    assert len(res_no_redirect.json()) == 2

    res_with_slash = seeded.get("/products/", follow_redirects=False)
    assert res_with_slash.status_code == 200


def test_orders_endpoint_trailing_slash_handling(seeded):
    """Orders endpoint responds properly both with and without trailing slash."""
    res_no_slash = seeded.get("/orders", follow_redirects=False)
    assert res_no_slash.status_code == 200

    res_with_slash = seeded.get("/orders/", follow_redirects=False)
    assert res_with_slash.status_code == 200


def test_order_and_cart_out_from_orm(seeded):
    """Bug 5: OrderOut, OrderItemOut, CartOut, CartItemOut must support model_validate from ORM objects."""
    order = Order(
        id=100,
        customer_id="cust100",
        status="paid",
        subtotal_minor=1299,
        discount_minor=0,
        total_minor=1299,
        idempotency_key="k100",
        items=[
            OrderItem(
                id=1,
                order_id=100,
                product_id=1,
                sku="NST-COFFEE",
                name="Northstar Coffee",
                unit_price_minor=1299,
                quantity=1,
            )
        ],
    )
    validated_order = OrderOut.model_validate(order)
    assert validated_order.id == 100
    assert validated_order.items[0].sku == "NST-COFFEE"

    validated_item = OrderItemOut.model_validate(order.items[0])
    assert validated_item.unit_price_minor == 1299


def test_discount_code_with_surrounding_whitespace(seeded):
    """Bug 6: Discount code with whitespace must be accepted and grant 10% discount."""
    add_item(seeded, "disc_user", 1, 2)  # 2598
    res = checkout(seeded, "disc_user", "disc-ws-1", discount_code="  WELCOME10  ")
    assert res.status_code == 200
    assert res.json()["discount_minor"] == 259
    assert res.json()["total_minor"] == 2339


def test_pricing_discount_whitespace_unit():
    """Bug 6 unit test: pricing.calculate handles whitespace in discount code."""
    p = Product(id=1, sku="S1", name="N1", price_minor=1000, inventory=10)
    item = CartItem(product_id=1, quantity=1, product=p)
    quote = calculate([item], "  welcome10  ")
    assert quote.discount_minor == 100
    assert quote.total_minor == 900


def test_customer_id_whitespace_normalization(seeded):
    """Bug 11: Customer ID whitespace is trimmed consistently."""
    res_add = seeded.post("/cart/  padded_cust  /items", json={"product_id": 1, "quantity": 1})
    assert res_add.status_code == 200
    assert res_add.json()["customer_id"] == "padded_cust"

    res_get = seeded.get("/cart/padded_cust")
    assert res_get.status_code == 200
    assert len(res_get.json()["items"]) == 1


def test_blank_customer_id_rejected(seeded):
    """Bug 11: Blank customer ID is rejected with 400."""
    res_get = seeded.get("/cart/%20%20")
    assert res_get.status_code == 400

    res_post = seeded.post("/cart/%20%20/items", json={"product_id": 1, "quantity": 1})
    assert res_post.status_code == 400

    res_checkout = checkout(seeded, "   ", "k-blank-cust")
    assert res_checkout.status_code == 400


def test_key_length_utility():
    """Bug 12: key_length returns stripped key length."""
    assert key_length("  abc  ") == 3
    assert key_length("") == 0
    assert key_length(None) == 0


def test_repeated_replays_consistent_response(seeded):
    """Replaying checkout multiple times returns identical response each time."""
    add_item(seeded, "repeat_user", 1, 1)
    res_first = checkout(seeded, "repeat_user", "multi-replay-1")
    assert res_first.status_code == 200
    first_body = res_first.json()

    for _ in range(5):
        res_replay = checkout(seeded, "repeat_user", "MULTI-REPLAY-1")
        assert res_replay.status_code == 200
        assert res_replay.json() == first_body

    # Orders count should still be 1
    orders = seeded.get("/orders").json()
    assert len(orders) == 1


def test_invalid_and_negative_quantities_in_cart(seeded):
    """Cart quantities outside [1, 99] or invalid types must be rejected with 422."""
    assert seeded.post("/cart/qty_user/items", json={"product_id": 1, "quantity": 0}).status_code == 422
    assert seeded.post("/cart/qty_user/items", json={"product_id": 1, "quantity": -5}).status_code == 422
    assert seeded.post("/cart/qty_user/items", json={"product_id": 1, "quantity": 100}).status_code == 422
    assert seeded.post("/cart/qty_user/items", json={"product_id": 1, "quantity": "invalid"}).status_code == 422


def test_add_nonexistent_product_to_cart_returns_404(seeded):
    """Adding a product that does not exist returns 404."""
    assert seeded.post("/cart/p404_user/items", json={"product_id": 99999, "quantity": 1}).status_code == 404
    assert seeded.post("/cart/p404_user/items", json={"product_id": -1, "quantity": 1}).status_code == 404


def test_product_and_order_lookup_edge_cases(seeded):
    """Looking up invalid or non-existent product or order IDs returns 404 or 422."""
    assert seeded.get("/products/9999").status_code == 404
    assert seeded.get("/products/-1").status_code == 404
    assert seeded.get("/products/invalid").status_code == 422

    assert seeded.get("/orders/9999").status_code == 404
    assert seeded.get("/orders/-1").status_code == 404
    assert seeded.get("/orders/invalid").status_code == 422


def test_key_length_boundary_validation(seeded):
    """Key of exactly 120 chars succeeds; 121 chars rejected with 400."""
    add_item(seeded, "boundary_user", 1, 1)
    k120 = "x" * 120
    assert checkout(seeded, "boundary_user", k120).status_code == 200

    add_item(seeded, "boundary_user2", 1, 1)
    k121 = "y" * 121
    assert checkout(seeded, "boundary_user2", k121).status_code == 400


def test_order_snapshot_immutability(seeded):
    """Catalogue modifications do not affect past order details."""
    add_item(seeded, "snap_user", 1, 1)
    order = checkout(seeded, "snap_user", "k-snap-1").json()
    assert order["items"][0]["unit_price_minor"] == 1299

    # Modify product in database
    db = SessionLocal()
    p = db.get(Product, 1)
    p.price_minor = 9999
    p.name = "Altered Name"
    db.commit()
    db.close()

    # Past order must retain purchase-time details
    fetched = seeded.get(f"/orders/{order['id']}").json()
    assert fetched["items"][0]["unit_price_minor"] == 1299
    assert fetched["items"][0]["name"] == "Northstar Coffee"


def test_declined_payment_creates_no_payment_attempt(seeded):
    """Declined checkout creates no Order and records no PaymentAttempt."""
    add_item(seeded, "no_attempt_user", 1, 1)
    res = checkout(seeded, "no_attempt_user", "k-no-attempt", payment_token="decline")
    assert res.status_code == 402

    db = SessionLocal()
    attempts = db.query(PaymentAttempt).all()
    orders = db.query(Order).all()
    db.close()
    assert len(orders) == 0
    assert len(attempts) == 0


def test_concurrent_idempotent_checkout(seeded):
    """Simulating concurrent checkout with identical idempotency key handles concurrency safely."""
    add_item(seeded, "concurrent_user", 1, 1)

    def do_checkout():
        return checkout(seeded, "concurrent_user", "CONCURRENT-KEY-1")

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(do_checkout) for _ in range(4)]
        results = [f.result() for f in futures]

    statuses = [r.status_code for r in results]
    assert all(s == 200 for s in statuses)

    # All should return the exact same order id
    order_ids = [r.json()["id"] for r in results]
    assert len(set(order_ids)) == 1

    # Inventory decremented exactly once (20 - 1 = 19)
    assert seeded.get("/products/1").json()["inventory"] == 19
