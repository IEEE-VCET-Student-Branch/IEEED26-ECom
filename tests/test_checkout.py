def test_checkout(seeded):
    seeded.post("/cart/alex/items", json={"product_id": 1, "quantity": 2})
    response = seeded.post("/checkout", headers={"Idempotency-Key": "order-alex-1"},
                           json={"customer_id": "alex", "payment_token": "tok"})
    assert response.status_code == 200
    assert response.json()["total_minor"] == 2598


def test_declined_payment_does_not_create_order(seeded):
    seeded.post("/cart/alex/items", json={"product_id": 1, "quantity": 1})
    response = seeded.post("/checkout", headers={"Idempotency-Key": "decline-1"},
                           json={"customer_id": "alex", "payment_token": "decline"})
    assert response.status_code == 402


def test_checkout_requires_key(seeded):
    assert seeded.post("/checkout", json={"customer_id": "alex", "payment_token": "tok"}).status_code == 400
