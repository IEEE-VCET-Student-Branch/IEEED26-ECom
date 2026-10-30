import threading
import time
from concurrent.futures import ThreadPoolExecutor

from fastapi import HTTPException

from app.database import SessionLocal
from app.models import Order, PaymentAttempt, Product


def add_item(client, customer_id, product_id, quantity):
    return client.post(
        f"/cart/{customer_id}/items",
        json={"product_id": product_id, "quantity": quantity},
    )


def checkout(client, customer_id, key, payment_token="tok", discount_code=None):
    body = {"customer_id": customer_id, "payment_token": payment_token}
    if discount_code is not None:
        body["discount_code"] = discount_code
    headers = {} if key is None else {"Idempotency-Key": key}
    return client.post("/checkout", headers=headers, json=body)


def state():
    db = SessionLocal()
    try:
        return (
            db.query(Order).count(),
            db.query(PaymentAttempt).count(),
            db.get(Product, 1).inventory,
        )
    finally:
        db.close()


def test_idempotency_key_is_case_insensitive_on_replay(seeded):
    add_item(seeded, "alex", 1, 1)
    first = checkout(seeded, "alex", "Case-Key-1")
    assert first.status_code == 200

    replay = checkout(seeded, "alex", "CASE-KEY-1")

    assert replay.status_code == 200
    assert replay.json() == first.json()
    assert state() == (1, 1, 19)


def test_idempotency_key_ignores_surrounding_whitespace_on_replay(seeded):
    add_item(seeded, "alex", 1, 1)
    first = checkout(seeded, "alex", "  spaced-key-1  ")
    assert first.status_code == 200

    replay = checkout(seeded, "alex", "spaced-key-1")

    assert replay.status_code == 200
    assert replay.json() == first.json()
    assert state() == (1, 1, 19)


def test_whitespace_only_idempotency_key_is_rejected(seeded):
    add_item(seeded, "alex", 1, 1)

    response = checkout(seeded, "alex", "   ")

    assert response.status_code == 400
    assert state() == (0, 0, 20)
    assert seeded.get("/cart/alex").json()["items"][0]["quantity"] == 1


def test_idempotency_key_length_is_checked_after_trimming(seeded):
    add_item(seeded, "alex", 1, 1)
    response = checkout(seeded, "alex", "  " + "k" * 120 + "  ")
    assert response.status_code == 200

    add_item(seeded, "bob", 1, 1)
    response = checkout(seeded, "bob", "k" * 121)
    assert response.status_code == 400

    add_item(seeded, "cara", 1, 1)
    response = checkout(seeded, "cara", "  " + "k" * 121 + "  ")
    assert response.status_code == 400


def test_exact_retry_returns_identical_body_and_does_not_duplicate_side_effects(seeded):
    add_item(seeded, "alex", 1, 2)
    first = checkout(seeded, "alex", "exact-replay-1")
    assert first.status_code == 200

    replay = checkout(seeded, "alex", "exact-replay-1")

    assert replay.status_code == 200
    assert replay.json() == first.json()
    assert state() == (1, 1, 18)


def test_different_logical_keys_create_independent_orders(seeded):
    add_item(seeded, "alex", 1, 1)
    first = checkout(seeded, "alex", "independent-1")
    assert first.status_code == 200

    add_item(seeded, "alex", 1, 1)
    second = checkout(seeded, "alex", "independent-2")
    assert second.status_code == 200

    assert first.json()["id"] != second.json()["id"]
    assert state() == (2, 2, 18)


def test_declined_key_is_reusable_and_records_no_attempt(seeded):
    add_item(seeded, "alex", 1, 1)
    declined = checkout(seeded, "alex", "decline-reuse-1", payment_token="decline")
    assert declined.status_code == 402
    assert state() == (0, 0, 20)
    assert seeded.get("/cart/alex").json()["items"][0]["quantity"] == 1

    completed = checkout(seeded, "alex", "decline-reuse-1", payment_token="tok")
    assert completed.status_code == 200
    assert state() == (1, 1, 19)


def test_decline_token_is_read_from_settings(seeded, monkeypatch):
    from app.config import get_settings

    monkeypatch.setenv("PAYMENT_DECLINE_TOKEN", "custom-decline")
    get_settings.cache_clear()
    try:
        add_item(seeded, "alex", 1, 1)
        declined = checkout(
            seeded, "alex", "custom-decline-1", payment_token="custom-decline"
        )
        assert declined.status_code == 402
        assert state() == (0, 0, 20)

        completed = checkout(seeded, "alex", "custom-decline-1", payment_token="tok")
        assert completed.status_code == 200
        assert state() == (1, 1, 19)
    finally:
        get_settings.cache_clear()


def test_failure_rolls_back_order_inventory_and_attempts_and_frees_key(seeded, monkeypatch):
    import app.services.order_service as order_service

    original_charge = order_service.payment.charge

    def unavailable(*args, **kwargs):
        raise HTTPException(503, "Payment provider unavailable")

    add_item(seeded, "alex", 1, 2)
    monkeypatch.setattr(order_service.payment, "charge", unavailable)

    failed = checkout(seeded, "alex", "rollback-1")
    assert failed.status_code == 503
    assert state() == (0, 0, 20)
    assert seeded.get("/cart/alex").json()["items"][0]["quantity"] == 2

    monkeypatch.setattr(order_service.payment, "charge", original_charge)
    completed = checkout(seeded, "alex", "rollback-1")
    assert completed.status_code == 200
    assert state() == (1, 1, 18)


def test_commit_failure_rolls_back_and_frees_key(seeded, monkeypatch):
    import pytest
    from sqlalchemy.exc import OperationalError
    from sqlalchemy.orm import Session

    original_commit = Session.commit

    def failing_commit(self):
        raise OperationalError("COMMIT", {}, Exception("simulated commit failure"))

    add_item(seeded, "alex", 1, 2)
    monkeypatch.setattr(Session, "commit", failing_commit)

    with pytest.raises(OperationalError):
        checkout(seeded, "alex", "commit-failure-1")

    monkeypatch.setattr(Session, "commit", original_commit)
    assert state() == (0, 0, 20)
    assert seeded.get("/cart/alex").json()["items"][0]["quantity"] == 2

    completed = checkout(seeded, "alex", "commit-failure-1")
    assert completed.status_code == 200
    assert state() == (1, 1, 18)


def test_concurrent_different_keys_cannot_oversell_inventory(seeded):
    db = SessionLocal()
    try:
        db.get(Product, 1).inventory = 1
        db.commit()
    finally:
        db.close()

    add_item(seeded, "alex", 1, 1)
    add_item(seeded, "bob", 1, 1)
    barrier = threading.Barrier(2)

    def attempt(customer_id, key):
        barrier.wait()
        return checkout(seeded, customer_id, key)

    with ThreadPoolExecutor(max_workers=2) as pool:
        first, second = list(
            pool.map(
                lambda args: attempt(*args),
                [("alex", "oversell-1"), ("bob", "oversell-2")],
            )
        )

    assert sorted([first.status_code, second.status_code]) == [200, 409]
    assert state() == (1, 1, 0)


def test_concurrent_logically_identical_keys_are_processed_once(seeded, monkeypatch):
    import app.services.order_service as order_service

    original_charge = order_service.payment.charge
    calls = []

    def slow_charge(token, amount):
        calls.append((token, amount))
        time.sleep(0.25)
        return original_charge(token, amount)

    monkeypatch.setattr(order_service.payment, "charge", slow_charge)
    add_item(seeded, "alex", 1, 2)

    barrier = threading.Barrier(2)

    def attempt(key):
        barrier.wait()
        return checkout(seeded, "alex", key)

    with ThreadPoolExecutor(max_workers=2) as pool:
        first, second = list(pool.map(attempt, [" Race-Key-1 ", "race-key-1"]))

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json() == second.json()
    assert calls == [("tok", 2598)]
    assert state() == (1, 1, 18)
