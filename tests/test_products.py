def test_products(seeded):
    response = seeded.get("/products")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_product_not_found(seeded):
    assert seeded.get("/products/999").status_code == 404


def test_product_shape(seeded):
    assert "price_minor" in seeded.get("/products/1").json()
