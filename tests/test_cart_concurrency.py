import threading
from concurrent.futures import ThreadPoolExecutor

from app.database import SessionLocal
from app.models import Cart

WORKERS = 8


def add_item(client, customer_id, product_id, quantity):
    return client.post(
        f"/cart/{customer_id}/items",
        json={"product_id": product_id, "quantity": quantity},
    )


def run_at_once(fn, args):
    barrier = threading.Barrier(len(args))

    def wrapped(arg):
        barrier.wait()
        return fn(arg)

    with ThreadPoolExecutor(max_workers=len(args)) as pool:
        return list(pool.map(wrapped, args))


def cart_lines(customer_id):
    db = SessionLocal()
    try:
        carts = db.query(Cart).filter(Cart.customer_id == customer_id).all()
        assert len(carts) == 1
        return [(item.product_id, item.quantity) for item in carts[0].items]
    finally:
        db.close()


def test_concurrent_first_adds_share_one_cart(seeded):
    results = run_at_once(
        lambda _: add_item(seeded, "race-new", 1, 1), [None] * WORKERS
    )

    assert [response.status_code for response in results] == [200] * WORKERS
    assert cart_lines("race-new") == [(1, WORKERS)]
    response = seeded.get("/cart/race-new")
    assert response.json()["items"][0]["quantity"] == WORKERS


def test_concurrent_adds_increment_exactly(seeded):
    assert add_item(seeded, "race-existing", 1, 1).status_code == 200

    results = run_at_once(
        lambda _: add_item(seeded, "race-existing", 1, 1), [None] * WORKERS
    )

    assert [response.status_code for response in results] == [200] * WORKERS
    assert cart_lines("race-existing") == [(1, 1 + WORKERS)]
    response = seeded.get("/cart/race-existing")
    assert response.json()["items"][0]["quantity"] == 1 + WORKERS
