def test_add_and_read_cart(seeded):
    response = seeded.post("/cart/alex/items", json={"product_id": 1, "quantity": 2})
    assert response.status_code == 200
    assert response.json()["subtotal_minor"] == 2598
    assert seeded.get("/cart/alex").json()["items"][0]["quantity"] == 2


def test_empty_cart_is_available(seeded):
    assert seeded.get("/cart/new-customer").json()["items"] == []


def test_repeat_add_increments_existing_line(seeded):
    seeded.post("/cart/alex/items", json={"product_id": 1, "quantity": 2})
    seeded.post("/cart/alex/items", json={"product_id": 1, "quantity": 1})
    cart = seeded.get("/cart/alex").json()
    assert len(cart["items"]) == 1
    assert cart["items"][0]["quantity"] == 3
    assert cart["subtotal_minor"] == 3897


def test_item_quantity_is_limited_per_request(seeded):
    response = seeded.post("/cart/alex/items", json={"product_id": 1, "quantity": 100})
    assert response.status_code == 422
