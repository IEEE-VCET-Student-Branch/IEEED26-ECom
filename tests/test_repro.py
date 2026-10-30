def add_item(client, customer_id, product_id, quantity):
    return client.post(f"/cart/{customer_id}/items",
                       json={"product_id": product_id, "quantity": quantity})


def checkout(client, customer_id, key, payment_token="tok", discount_code=None):
    body = {"customer_id": customer_id, "payment_token": payment_token}
    if discount_code is not None:
        body["discount_code"] = discount_code
    return client.post("/checkout", headers={"Idempotency-Key": key}, json=body)

def test_idempotency_key_casing(seeded):
    add_item(seeded, "alex", 1, 1)
    # First checkout
    res1 = checkout(seeded, "alex", "KEY-1")
    assert res1.status_code == 200
    order_id1 = res1.json()["id"]
    
    # Second checkout with different casing
    res2 = checkout(seeded, "alex", "key-1")
    assert res2.status_code == 200
    # THIS SHOULD FAIL IF BUG IS PRESENT
    assert res2.json()["id"] == order_id1, "Casing mismatch: new order created instead of returning existing"

def test_idempotency_key_whitespace(seeded):
    add_item(seeded, "alex", 1, 1)
    # First checkout
    res1 = checkout(seeded, "alex", "KEY-2")
    assert res1.status_code == 200, res1.text
    order_id1 = res1.json()["id"]
    
    # Second checkout with extra whitespace
    res2 = checkout(seeded, "alex", "  KEY-2  ")
    assert res2.status_code == 200, res2.text
    assert res2.json()["id"] == order_id1
