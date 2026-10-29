def test_add_and_read_cart(seeded):
    response = seeded.post("/cart/alex/items", json={"product_id": 1, "quantity": 2})
    assert response.status_code == 200
    assert response.json()["subtotal_minor"] == 2598
    assert seeded.get("/cart/alex").json()["items"][0]["quantity"] == 2


def test_empty_cart_is_available(seeded):
    assert seeded.get("/cart/new-customer").json()["items"] == []
