def test_idempotent_retry_case_and_whitespace(seeded):
    seeded.post("/cart/alex/items", json={"product_id": 1, "quantity": 1})
    r1 = seeded.post("/checkout", headers={"Idempotency-Key": "Order-Alex-1"},
                     json={"customer_id": "alex", "payment_token": "tok"})
    assert r1.status_code == 200
    # Retry with differing case and surrounding whitespace
    r2 = seeded.post("/checkout", headers={"Idempotency-Key": "  order-alex-1  "},
                     json={"customer_id": "alex", "payment_token": "tok"})
    assert r2.status_code == 200
    assert r2.json() == r1.json()
    assert seeded.get("/products/1").json()["inventory"] == 19


def test_reject_blank_or_whitespace_key(seeded):
    seeded.post("/cart/alex/items", json={"product_id": 1, "quantity": 1})
    res = seeded.post("/checkout", headers={"Idempotency-Key": "   "},
                      json={"customer_id": "alex", "payment_token": "tok"})
    assert res.status_code == 400
