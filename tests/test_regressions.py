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


def test_configurable_payment_decline_token(seeded, monkeypatch):
    from app.config import get_settings
    monkeypatch.setenv("PAYMENT_DECLINE_TOKEN", "custom-decline")
    get_settings.cache_clear()
    seeded.post("/cart/alex/items", json={"product_id": 1, "quantity": 1})
    res_decline = seeded.post("/checkout", headers={"Idempotency-Key": "dec-custom-1"},
                              json={"customer_id": "alex", "payment_token": "custom-decline"})
    assert res_decline.status_code == 402
    res_ok = seeded.post("/checkout", headers={"Idempotency-Key": "dec-custom-2"},
                         json={"customer_id": "alex", "payment_token": "decline"})
    assert res_ok.status_code == 200


def test_products_endpoint_with_and_without_trailing_slash(seeded):
    r_no_slash = seeded.get("/products", follow_redirects=False)
    assert r_no_slash.status_code == 200
    r_with_slash = seeded.get("/products/", follow_redirects=False)
    assert r_with_slash.status_code == 200
    assert r_no_slash.json() == r_with_slash.json()
