## Team

Team name: Final Commit Debuggers

## Summary

This PR resolves four defects across checkout idempotency, payment configuration, header validation, and catalog routing in Northstar Market:
1. **Idempotency key normalization**: Fixes duplicate orders, multiple inventory decrements, and repeated charges caused by inconsistent key handling when clients retry checkout with surrounding whitespace or different letter case.
2. **Configurable payment decline token**: Enables dynamic decline token configuration via `PAYMENT_DECLINE_TOKEN` environment setting instead of a hardcoded `"decline"` string.
3. **Blank idempotency key validation**: Enforces HTTP 400 rejection for whitespace-only idempotency keys as specified in `docs/requirements.md`.
4. **Direct catalog retrieval**: Fixes `GET /products` returning a 307 Temporary Redirect by supporting `/products` directly with HTTP 200.

All 28 visible test suite tests pass, visible test files and `docs/requirements.md` remain completely unmodified, and all behavioral requirements are satisfied.

## Bug inventory

List every defect found, major and minor, including ones not fixed here. Add rows as needed.

| # | Severity | Symptom | Root cause | Location | Fix | Verified by |
|---|----------|---------|------------|----------|-----|-------------|
| 1 | major | Retrying checkout with an idempotency key containing different casing or surrounding whitespace produces duplicate orders, decrements inventory multiple times, and charges payment repeatedly (Incident #047, BR-882, BR-894). | Inconsistent idempotency key normalization: `require_idempotency_key` returned raw header, `find_order` queried using the raw header, while `create_order` stored `key.lower()` (without stripping whitespace). | `app/dependencies.py`, `app/services/order_service.py`, `app/utils/idempotency.py` | Canonicalize keys using `.strip().lower()` in `require_idempotency_key` and `find_order`, and store the canonical key in `create_order`. | Test replaying checkout with `"key-1"`, `"  key-1  "`, and `"KEY-1"`; verified identical order returned and inventory decremented once. |
| 2 | major | Setting `PAYMENT_DECLINE_TOKEN` environment variable has no effect. The service always checks hardcoded `"decline"`, failing to decline configured tokens and incorrectly declining when a custom token is set. | Hardcoded string literal `"decline"` in `app/services/payment.py` instead of referencing `get_settings().payment_decline_token`. | `app/services/payment.py` (`charge`, `is_decline`) | Read decline token from `get_settings().payment_decline_token`. | Verified with `PAYMENT_DECLINE_TOKEN=custom_decline`; verified `"custom_decline"` returns 402 while `"decline"` succeeds with 200. |
| 3 | minor | Whitespace-only `Idempotency-Key` header (e.g. `"   "`) is accepted instead of being rejected with HTTP 400, creating an order with an empty key `""`. | `require_idempotency_key` checked `if not idempotency_key:` which is `True` for whitespace strings with length <= 120. | `app/dependencies.py` (`require_idempotency_key`) | Reject blank normalized keys: `if not normalized or len(normalized) > 120: raise HTTPException(400)`. | Verified checkout with `Idempotency-Key: "   "` returns HTTP 400. |
| 4 | minor | `GET /products` returns a 307 Temporary Redirect to `/products/` instead of directly returning the catalog with HTTP 200. | Route was defined with `@router.get("/")` on prefix `/products` instead of `@router.get("")`. | `app/api/products.py` (`list_products`) | Add `@router.get("")` route handler so `/products` responds with 200 directly. | Verified `client.get("/products", follow_redirects=False)` returns HTTP 200. |

## Defects not fixed

None. All four defects identified during investigation have been fixed in this PR.

## Verification

Commands run:

```bash
python -m pytest -v
```

Visible suite result:

```text
============================= test session starts =============================
platform win32 -- Python 3.14.7, pytest-8.4.2, pluggy-1.7.0 -- C:\Users\acer\AppData\Local\Python\pythoncore-3.14-64\python.exe
cachedir: .pytest_cache
rootdir: D:\IEEED26-ECom
configfile: pyproject.toml
testpaths: tests
plugins: anyio-4.15.1, langsmith-0.14.1
collecting ... collected 28 items

tests/test_cart.py::test_add_and_read_cart PASSED                        [  3%]
tests/test_cart.py::test_empty_cart_is_available PASSED                  [  7%]
tests/test_cart.py::test_repeat_add_increments_existing_line PASSED      [ 10%]
tests/test_cart.py::test_item_quantity_is_limited_per_request PASSED     [ 14%]
tests/test_checkout.py::test_checkout PASSED                             [ 17%]
tests/test_checkout.py::test_declined_payment_does_not_create_order PASSED [ 21%]
tests/test_checkout.py::test_checkout_requires_key PASSED                [ 25%]
tests/test_checkout.py::test_checkout_rejects_overlong_key PASSED        [ 28%]
tests/test_checkout.py::test_checkout_requires_non_empty_cart PASSED     [ 32%]
tests/test_checkout.py::test_checkout_clears_cart PASSED                 [ 35%]
tests/test_checkout.py::test_checkout_decrements_inventory_once PASSED   [ 39%]
tests/test_checkout.py::test_declined_payment_leaves_cart_and_inventory_intact PASSED [ 42%]
tests/test_checkout.py::test_insufficient_inventory_is_rejected PASSED   [ 46%]
tests/test_checkout.py::test_welcome_discount_applies_at_checkout PASSED [ 50%]
tests/test_checkout.py::test_multi_item_totals PASSED                    [ 53%]
tests/test_checkout.py::test_order_lines_snapshot_purchase_details PASSED [ 57%]
tests/test_health.py::test_health PASSED                                 [ 60%]
tests/test_orders.py::test_order_retrieval PASSED                        [ 64%]
tests/test_orders.py::test_missing_order PASSED                          [ 67%]
tests/test_orders.py::test_order_list_starts_empty PASSED                [ 71%]
tests/test_orders.py::test_checkout_appears_in_order_list PASSED         [ 75%]
tests/test_pricing.py::test_welcome_discount PASSED                      [ 78%]
tests/test_pricing.py::test_unknown_discount_is_ignored PASSED           [ 82%]
tests/test_pricing.py::test_discount_code_is_case_insensitive PASSED     [ 85%]
tests/test_pricing.py::test_discount_rounds_down PASSED                  [ 89%]
tests/test_products.py::test_products PASSED                             [ 92%]
tests/test_products.py::test_product_not_found PASSED                    [ 96%]
tests/test_product_shape PASSED                                           [100%]

============================= 28 passed in 6.89s ==============================
```

Before/after reproduction for each fixed defect:

1. **Idempotency retry with whitespace/case:**
   - *Before*: Initial checkout with `"key-ws"` creates Order #1. Retry with `"  key-ws  "` fails lookup in `find_order`, creates Order #2, and decrements inventory twice (inventory goes from 20 -> 18).
   - *After*: Both requests resolve to canonical key `"key-ws"`. Retry returns Order #1 with identical response body, no new order created, inventory decremented exactly once (inventory remains 19).

2. **Configurable decline token:**
   - *Before*: With `PAYMENT_DECLINE_TOKEN=custom_decline`, payment with token `"custom_decline"` returned 200 (not declined), and `"decline"` returned 402.
   - *After*: Payment with `"custom_decline"` returns 402 Payment Declined; payment with `"decline"` succeeds (status 200).

3. **Blank / whitespace-only idempotency key:**
   - *Before*: Header `Idempotency-Key: "   "` passed validation with HTTP 200, creating an order with `idempotency_key=""`.
   - *After*: Header `Idempotency-Key: "   "` is rejected with HTTP 400 `"Idempotency-Key header is required"`.

4. **Catalog GET /products redirect:**
   - *Before*: `client.get('/products', follow_redirects=False)` returned HTTP 307 Temporary Redirect to `/products/`.
   - *After*: `client.get('/products', follow_redirects=False)` returns HTTP 200 OK directly with catalogue list.

## Checklist

- [x] I have read `docs/requirements.md` and `docs/submission.md`
- [x] No changes to `tests/` or `docs/requirements.md`
- [x] A clean checkout runs using the steps in the README
- [x] Retry and decline behavior matches `docs/requirements.md`
- [x] Every item in the bug inventory is fixed or listed under "Defects not fixed"
- [x] No database files, secrets, or generated artifacts are committed
- [x] I understand this PR is evaluated once, when opened, and will not be merged
