## Team

Team name:Agasthya 

## Summary

This pull request implements and verifies systematic corrections for all 6 confirmed defects identified across the Northstar Market codebase to satisfy the authoritative behavioral specification in `docs/requirements.md`:

1. **Idempotency Key Normalization (B-001)**: Normalized `Idempotency-Key` (case-folding and whitespace trimming) across header validation, database lookup, and order model persistence. Replaying checkouts with different casing or surrounding whitespace now retrieves the original order rather than failing with `400 {"detail":"Cart is empty"}`.

2. **Blank Idempotency Key Validation (B-002)**: Updated `require_idempotency_key` in `app/dependencies.py` to validate that keys are non-blank after stripping whitespace, correctly returning `HTTP 400` on blank/whitespace-only keys.
3. **Configurable Payment Decline Token (B-003)**: Updated `app/services/payment.py` (`charge` and `is_decline`) to dynamically read `get_settings().payment_decline_token` instead of hardcoding literal `"decline"`, honoring the `PAYMENT_DECLINE_TOKEN` environment setting.
4. **Catalogue Route Normalization (B-004)**: Added `@router.get("")` decorator to `app/api/products.py` so `GET /products` returns `HTTP 200 OK` directly without issuing a `307 Temporary Redirect` to `/products/`.
5. **Discount Code Whitespace Handling (B-005)**: Updated `discount_for` in `app/services/pricing.py` to strip surrounding whitespace before validating against `"WELCOME10"`, correctly granting the 10% discount.
6. **Pytest Discovery Configuration (B-006)**: Added `pythonpath = ["."]` to `[tool.pytest.ini_options]` in `pyproject.toml` to ensure direct CLI invocation of `pytest` from the repository root succeeds cleanly.

## Bug inventory

List every defect found, major and minor, including ones not fixed here. Add rows as needed.

| # | Severity | Symptom | Root cause | Location | Fix | Verified by |
|---|----------|---------|------------|----------|-----|-------------|
| 1 | major | Replaying checkout with differing casing (e.g. `MY-KEY` vs `my-key`) or surrounding whitespace returns `400 {"detail":"Cart is empty"}` instead of returning the existing order | `find_order` queried `Order.idempotency_key == key` without trimming or lowercasing; `create_order` stored `key.lower()` without trimming whitespace; SQLite string comparison is case-sensitive | `app/utils/idempotency.py` (`find_order`, `key_length`), `app/services/order_service.py` (`create_order`), `app/dependencies.py` (`require_idempotency_key`) | Implemented: Normalized key via `.strip().lower()` in dependency validation, lookup query, and order model persistence | Retried checkout with differing case and surrounding whitespace; verified 200 OK and identical order representation returned |
| 2 | major | Blank/whitespace-only `Idempotency-Key` (e.g. `"   "`) is accepted with HTTP 200 instead of being rejected with HTTP 400 | `require_idempotency_key` checked `if not idempotency_key or len(idempotency_key) > 120:`, which evaluates to False for non-empty whitespace strings | `app/dependencies.py` (`require_idempotency_key`) | Implemented: Stripped key first and validated `if not cleaned or len(cleaned) > 120: raise HTTPException(400)` | Sent `POST /checkout` with whitespace header `"   "`, empty string `""`, and missing header; verified HTTP 400 returned |
| 3 | major | Setting `PAYMENT_DECLINE_TOKEN` environment variable has no effect; hardcoded `"decline"` token declines while custom token succeeds | `app/services/payment.py` hardcoded comparison with literal `"decline"` instead of using `get_settings().payment_decline_token` | `app/services/payment.py` (`is_decline`, `charge`) | Implemented: Replaced hardcoded string with `get_settings().payment_decline_token` | Set `PAYMENT_DECLINE_TOKEN=custom_fail_token`; verified `custom_fail_token` returns HTTP 402 and `"decline"` returns HTTP 200 |
| 4 | minor | `GET /products` returns HTTP 307 Temporary Redirect instead of returning product catalogue directly | Endpoint was registered as `@router.get("/")` on an APIRouter with `prefix="/products"`, making `/products/` canonical | `app/api/products.py` (`list_products`) | Implemented: Added `@router.get("")` route decorator to handle `/products` directly | Sent `GET /products` with `follow_redirects=False`; verified HTTP 200 and product list returned |
| 5 | minor | Discount code with surrounding whitespace (e.g. `" welcome10 "`) is ignored and yields 0 discount | `discount_for` checked `discount_code.upper() == "WELCOME10"` without stripping surrounding whitespace | `app/services/pricing.py` (`discount_for`) | Implemented: Updated to check `discount_code and discount_code.strip().upper() == "WELCOME10"` | Sent `POST /checkout` with `"  welcome10  "`; verified 10% discount (`259`) applied |
| 6 | minor | Running `pytest` directly in root fails with `ModuleNotFoundError: No module named 'app'` | `pyproject.toml` omitted `pythonpath = ["."]` in `[tool.pytest.ini_options]` | `pyproject.toml` (`[tool.pytest.ini_options]`) | Implemented: Added `pythonpath = ["."]` under `[tool.pytest.ini_options]` | Executed `pytest` directly from repository root; verified all 28 tests collected and passed |

### Suspected / Unverified Issues

| # | Severity | Symptom | Root cause | Location | Status / Limitation |
|---|----------|---------|------------|----------|---------------------|
| S-1 | suspected | Unused customer ID validation dependency | `validate_customer_id` is defined in `app/dependencies.py` but never referenced in `app/api/cart.py` or `app/api/checkout.py` | `app/dependencies.py` (line 13) | Informational: Requirements do not mandate customer ID whitespace trimming; kept as-is to avoid modifying public dependency signatures |
| S-2 | suspected | Potential non-deterministic line item ordering | `Cart.items` and `Order.items` relationships in `app/models.py` lack an explicit `order_by` clause | `app/models.py` (lines 25, 49) | Informational: Single-connection SQLite default query order follows primary key insertion order, matching verified behavior |

## Defects not fixed

None. All 6 confirmed defects identified in the bug inventory have been successfully corrected and verified.

## Verification

Commands run:

```bash
.\.venv\Scripts\pytest -v
```

Visible suite result:

```text
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-8.4.2, pluggy-1.7.0 -- D:\IEEE\IEEED26-ECom\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: D:\IEEE\IEEED26-ECom
configfile: pyproject.toml
testpaths: tests
plugins: anyio-4.15.1
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
tests/test_products.py::test_product_shape PASSED                        [100%]

======================== 28 passed, 1 warning in 3.12s ========================
```

Before/after reproduction for each fixed defect:

1. **Defect 1 (B-001 — Idempotent retry casing and whitespace)**:
   - *Before*: `POST /checkout` with `Idempotency-Key: "my-lower-key"` succeeded, but retry with `Idempotency-Key: "MY-LOWER-KEY"` or `"  key-with-space  "` returned HTTP 400 `{"detail":"Cart is empty"}`.
   - *After*: Retrying checkout with differing casing or whitespace returns HTTP 200 with the exact same order representation, without creating a second order or decrementing inventory again.

2. **Defect 2 (B-002 — Blank Idempotency-Key)**:
   - *Before*: `POST /checkout` with `Idempotency-Key: "   "` succeeded with HTTP 200 because `not idempotency_key` evaluated to False and length was <= 120.
   - *After*: Returns HTTP 400 `{"detail":"Idempotency-Key header is required"}`.

3. **Defect 3 (B-003 — Configurable decline token)**:
   - *Before*: With `PAYMENT_DECLINE_TOKEN=custom_fail_token`, `POST /checkout` with `payment_token="custom_fail_token"` returned HTTP 200, while `"decline"` returned HTTP 402.
   - *After*: `POST /checkout` with token `custom_fail_token` returns HTTP 402 (declined), while `"decline"` returns HTTP 200 (paid).

4. **Defect 4 (B-004 — GET /products routing)**:
   - *Before*: `client.get("/products", follow_redirects=False)` returned HTTP 307 Temporary Redirect to `/products/` instead of returning the catalogue.
   - *After*: Returns HTTP 200 with product catalogue items directly.

5. **Defect 5 (B-005 — Discount code whitespace)**:
   - *Before*: `POST /checkout` with `discount_code="  welcome10  "` returned `discount_minor: 0`.
   - *After*: Returns `discount_minor: 259` and `total_minor: 2339` (10% discount applied).

6. **Defect 6 (B-006 — Direct pytest execution)**:
   - *Before*: Running `pytest` directly from root failed with `ModuleNotFoundError: No module named 'app'`.
   - *After*: Running `pytest` runs and passes all 28 tests cleanly.

## Checklist

- [x] I have read `docs/requirements.md` and `docs/submission.md`
- [x] No changes to `tests/` or `docs/requirements.md`
- [x] A clean checkout runs using the steps in the README
- [x] Retry and decline behavior matches `docs/requirements.md`
- [x] Every item in the bug inventory is fixed or listed under "Defects not fixed"
- [x] No database files, secrets, or generated artifacts are committed
- [x] I understand this PR is evaluated once, when opened, and will not be merged
