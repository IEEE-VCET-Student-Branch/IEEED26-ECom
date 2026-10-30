## Team

Team name:Agasthya 

## Summary

This PR resolves all functional defects and regressions identified in the Northstar Market service to satisfy the authoritative behavioral specification in `docs/requirements.md`:

1. **Idempotency Key Normalization**: Normalized `Idempotency-Key` (case and whitespace) across request extraction, database query, and order creation so that checkout replays with different letter case or surrounding whitespace return the existing order rather than failing with `400 Cart is empty`.
2. **Blank Idempotency Key Validation**: Added non-blank validation to `require_idempotency_key` so whitespace-only keys (e.g. `"   "`) are rejected with `HTTP 400`.
3. **Configurable Payment Decline Token**: Updated `app/services/payment.py` to read `get_settings().payment_decline_token` rather than hardcoding `"decline"`, honoring the `PAYMENT_DECLINE_TOKEN` environment setting.
4. **Catalogue Endpoint Routing**: Added `@router.get("")` route to `app/api/products.py` so `GET /products` returns `200 OK` directly without returning a `307 Temporary Redirect`.
5. **Discount Code Whitespace Handling**: Updated `discount_for` in `app/services/pricing.py` to strip surrounding whitespace before validating against `"WELCOME10"`.
6. **Pytest Discovery Configuration**: Added `pythonpath = ["."]` to `[tool.pytest.ini_options]` in `pyproject.toml` to ensure `pytest` can be executed directly from root as specified in the README.

## Bug inventory

List every defect found, major and minor, including ones not fixed here. Add rows as needed.

| # | Severity | Symptom | Root cause | Location | Fix | Verified by |
|---|----------|---------|------------|----------|-----|-------------|
| 1 | major | Replaying checkout with differing casing (e.g. `MY-KEY` vs `my-key`) or surrounding whitespace returns `400 {"detail":"Cart is empty"}` instead of returning the existing order | `find_order` queried `Order.idempotency_key == key` without trimming or lowercasing; `create_order` stored `key.lower()` without trimming whitespace; SQLite string comparison is case-sensitive | `app/utils/idempotency.py` (`find_order`, `key_length`), `app/services/order_service.py` (`create_order`), `app/dependencies.py` (`require_idempotency_key`) | Normalized key via `.strip().lower()` in dependency validation, lookup query, and order model persistence | Retried checkout with differing case and surrounding whitespace; verified 200 OK and identical order returned |
| 2 | major | Blank/whitespace-only `Idempotency-Key` (e.g. `"   "`) is accepted with HTTP 200 instead of being rejected with HTTP 400 | `require_idempotency_key` checked `if not idempotency_key or len(idempotency_key) > 120:`, which evaluates to False for non-empty whitespace strings | `app/dependencies.py` (`require_idempotency_key`) | Stripped key first and validated `if not cleaned or len(cleaned) > 120: raise HTTPException(400)` | Sent `POST /checkout` with whitespace header `"   "`; verified HTTP 400 returned |
| 3 | major | Setting `PAYMENT_DECLINE_TOKEN` environment variable has no effect; hardcoded `"decline"` token declines while custom token succeeds | `app/services/payment.py` hardcoded comparison with literal `"decline"` instead of using `get_settings().payment_decline_token` | `app/services/payment.py` (`is_decline`, `charge`) | Replaced hardcoded string with `get_settings().payment_decline_token` | Set `PAYMENT_DECLINE_TOKEN=custom_decline`; verified `custom_decline` returns HTTP 402 and `"decline"` returns HTTP 200 |
| 4 | minor | `GET /products` returns HTTP 307 Temporary Redirect instead of returning product catalogue directly | Endpoint was registered as `@router.get("/")` on an APIRouter with `prefix="/products"`, making `/products/` canonical | `app/api/products.py` (`list_products`) | Added `@router.get("")` route decorator to handle `/products` directly | Sent `GET /products` with `follow_redirects=False`; verified HTTP 200 and product list returned |
| 5 | minor | Discount code with surrounding whitespace (e.g. `" welcome10 "`) is ignored and yields 0 discount | `discount_for` checked `discount_code.upper() == "WELCOME10"` without stripping surrounding whitespace | `app/services/pricing.py` (`discount_for`) | Updated to check `discount_code and discount_code.strip().upper() == "WELCOME10"` | Sent `POST /checkout` with `"  welcome10  "`; verified 10% discount (`259`) applied |
| 6 | minor | Running `pytest` directly in root fails with `ModuleNotFoundError: No module named 'app'` | `pyproject.toml` omitted `pythonpath = ["."]` in `[tool.pytest.ini_options]` | `pyproject.toml` (`[tool.pytest.ini_options]`) | Added `pythonpath = ["."]` under `[tool.pytest.ini_options]` | Executed `pytest` directly from repository root; verified all 28 tests collected and passed |

## Defects not fixed

None. All 6 defects identified during analysis have been implemented and verified.

## Verification

Commands run:

```bash
pytest
```

Visible suite result:

```text
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-8.4.2, pluggy-1.7.0
rootdir: D:\IEEE\IEEED26-ECom
configfile: pyproject.toml
testpaths: tests
plugins: anyio-4.15.1
collected 28 items

tests\test_cart.py ....                                                  [ 14%]
tests\test_checkout.py ............                                      [ 57%]
tests\test_health.py .                                                   [ 60%]
tests\test_orders.py ....                                                [ 75%]
tests\test_pricing.py ....                                               [ 89%]
tests\test_products.py ...                                               [100%]

======================== 28 passed, 1 warning in 3.08s ========================
```

Before/after reproduction for each fixed defect:

1. **Defect 1: Idempotent checkout retry with differing case or whitespace**
   - **Before**: `POST /checkout` with `Idempotency-Key: "my-lower-key"` followed by retry with `Idempotency-Key: "MY-LOWER-KEY"` or `"  key-with-space  "` returned HTTP 400 `{"detail":"Cart is empty"}`.
   - **After**: Retry with differing casing or surrounding whitespace returns HTTP 200 with the exact same order details (`id`, line items, totals) and does not decrement inventory or create duplicate orders.

2. **Defect 2: Blank Idempotency-Key header**
   - **Before**: `POST /checkout` with `Idempotency-Key: "   "` succeeded with HTTP 200.
   - **After**: Returns HTTP 400 `{"detail":"Idempotency-Key header is required"}`.

3. **Defect 3: Configurable PAYMENT_DECLINE_TOKEN**
   - **Before**: With `PAYMENT_DECLINE_TOKEN=custom_decline`, `POST /checkout` with token `custom_decline` returned HTTP 200 (payment succeeded), while token `"decline"` returned HTTP 402.
   - **After**: `POST /checkout` with token `custom_decline` returns HTTP 402 (declined), while `"decline"` returns HTTP 200 (paid).

4. **Defect 4: GET /products routing**
   - **Before**: `client.get("/products", follow_redirects=False)` returned HTTP 307 Temporary Redirect.
   - **After**: Returns HTTP 200 with product catalogue items.

5. **Defect 5: Discount code whitespace**
   - **Before**: `POST /checkout` with `discount_code="  welcome10  "` returned `discount_minor: 0`.
   - **After**: Returns `discount_minor: 259` and `total_minor: 2339`.

6. **Defect 6: Direct pytest execution**
   - **Before**: Running `pytest` returned `ModuleNotFoundError: No module named 'app'`.
   - **After**: Running `pytest` executes successfully with 28 passed tests.

## Checklist

- [x] I have read `docs/requirements.md` and `docs/submission.md`
- [x] No changes to `tests/` or `docs/requirements.md`
- [x] A clean checkout runs using the steps in the README
- [x] Retry and decline behavior matches `docs/requirements.md`
- [x] Every item in the bug inventory is fixed or listed under "Defects not fixed"
- [x] No database files, secrets, or generated artifacts are committed
- [x] I understand this PR is evaluated once, when opened, and will not be merged
