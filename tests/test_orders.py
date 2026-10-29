def test_order_retrieval(seeded):
    seeded.post("/cart/alex/items", json={"product_id": 1, "quantity": 1})
    order = seeded.post("/checkout", headers={"Idempotency-Key": "order-1"},
                        json={"customer_id": "alex", "payment_token": "tok"}).json()
    assert seeded.get(f"/orders/{order['id']}").json()["id"] == order["id"]


def test_missing_order(seeded):
    assert seeded.get("/orders/999").status_code == 404


def test_order_list_starts_empty(seeded):
    assert seeded.get("/orders").json() == []
