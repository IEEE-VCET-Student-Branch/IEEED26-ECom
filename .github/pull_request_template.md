## Team

Team name:Agasthya 

## Summary

This pull request template documents the comprehensive repository audit findings conducted against the behavioral contract in `docs/requirements.md` and the submission guidelines in `docs/submission.md`.

This audit identified 6 confirmed defects (3 major, 3 minor) and 2 suspected/unverified items across idempotency handling, decline token configuration, route handling, pricing calculations, and testing configuration:
- In the initial codebase, checkout retries failed whenever the `Idempotency-Key` had different casing or surrounding whitespace due to case-sensitive SQLite comparison and unnormalized keys.
- Blank/whitespace-only `Idempotency-Key` headers were accepted with HTTP 200 instead of being rejected with HTTP 400.
- Payment decline tokens were hardcoded to `"decline"`, ignoring the `PAYMENT_DECLINE_TOKEN` environment setting.
- `GET /products` returned an HTTP 307 Temporary Redirect instead of returning the catalogue directly with HTTP 200 OK.
- Discount code comparison did not strip surrounding whitespace, causing valid codes with spaces to grant 0 discount.
- Direct invocation of `pytest` from repository root failed due to missing `pythonpath` in `pyproject.toml`.

Note: This document records audit findings. As this task was strictly an audit-and-documentation task, no fixes were implemented during this audit, and proposed fixes are documented as proposed corrections pending implementation.

## Bug inventory

List every defect found, major and minor, including ones not fixed here. Add rows as needed.

| # | Severity | Symptom | Root cause | Location | Fix | Verified by |
|---|----------|---------|------------|----------|-----|-------------|
| 1 | major | Replaying checkout with differing casing (e.g. `MY-KEY` vs `my-key`) or surrounding whitespace returns `400 {"detail":"Cart is empty"}` instead of returning the existing order | `find_order` queried `Order.idempotency_key == key` without trimming or lowercasing; `create_order` stored `key.lower()` without trimming whitespace; SQLite string comparison is case-sensitive | `app/utils/idempotency.py` (`find_order`, `key_length`), `app/services/order_service.py` (`create_order`), `app/dependencies.py` (`require_idempotency_key`) | Proposed fix — not implemented: Normalize key via `.strip().lower()` in dependency validation, lookup query, and order model persistence | Reproduced via TestClient: initial checkout with `my-lower-key` succeeded; retry with `MY-LOWER-KEY` returned HTTP 400 `{"detail":"Cart is empty"}` |
| 2 | major | Blank/whitespace-only `Idempotency-Key` (e.g. `"   "`) is accepted with HTTP 200 instead of being rejected with HTTP 400 | `require_idempotency_key` checked `if not idempotency_key or len(idempotency_key) > 120:`, which evaluates to False for non-empty whitespace strings | `app/dependencies.py` (`require_idempotency_key`) | Proposed fix — not implemented: Strip key first and validate `if not cleaned or len(cleaned) > 120: raise HTTPException(400)` | Reproduced via TestClient: `POST /checkout` with header `Idempotency-Key: "   "` returned HTTP 200 instead of HTTP 400 |
| 3 | major | Setting `PAYMENT_DECLINE_TOKEN` environment variable has no effect; hardcoded `"decline"` token declines while custom token succeeds | `app/services/payment.py` hardcoded comparison with literal `"decline"` instead of using `get_settings().payment_decline_token` | `app/services/payment.py` (`is_decline`, `charge`) | Proposed fix — not implemented: Replace hardcoded string with `get_settings().payment_decline_token` | Reproduced via TestClient with `PAYMENT_DECLINE_TOKEN=custom_decline`: token `custom_decline` returned HTTP 200 (payment succeeded), while `"decline"` returned HTTP 402 |
| 4 | minor | `GET /products` returns HTTP 307 Temporary Redirect instead of returning product catalogue directly | Endpoint was registered as `@router.get("/")` on an APIRouter with `prefix="/products"`, making `/products/` canonical | `app/api/products.py` (`list_products`) | Proposed fix — not implemented: Add `@router.get("")` route decorator to handle `/products` directly | Reproduced via TestClient with `follow_redirects=False`: `GET /products` returned status code 307 redirect instead of 200 |
| 5 | minor | Discount code with surrounding whitespace (e.g. `" welcome10 "`) is ignored and yields 0 discount | `discount_for` checked `discount_code.upper() == "WELCOME10"` without stripping surrounding whitespace | `app/services/pricing.py` (`discount_for`) | Proposed fix — not implemented: Update to check `discount_code and discount_code.strip().upper() == "WELCOME10"` | Reproduced via TestClient: `POST /checkout` with `"  welcome10  "` returned `discount_minor: 0` instead of 10% discount (`259`) |
| 6 | minor | Running `pytest` directly in root fails with `ModuleNotFoundError: No module named 'app'` | `pyproject.toml` omitted `pythonpath = ["."]` in `[tool.pytest.ini_options]` | `pyproject.toml` (`[tool.pytest.ini_options]`) | Proposed fix — not implemented: Add `pythonpath = ["."]` under `[tool.pytest.ini_options]` in `pyproject.toml` | Reproduced by running `pytest` from repository root: failed test collection with `ModuleNotFoundError: No module named 'app'` |

### Suspected / Unverified Issues

| # | Severity | Symptom | Root cause | Location | Status / Limitation |
|---|----------|---------|------------|----------|---------------------|
| S-1 | suspected | Unused customer ID validation dependency | `validate_customer_id` is defined in `app/dependencies.py` but never referenced in `app/api/cart.py` or `app/api/checkout.py` | `app/dependencies.py` (line 13) | Unverified: Requirements do not explicitly mandate customer ID whitespace trimming, but unreferenced dependency suggests possible incomplete integration |
| S-2 | suspected | Potential non-deterministic line item ordering | `Cart.items` and `Order.items` relationships in `app/models.py` lack an explicit `order_by` clause | `app/models.py` (lines 25, 49) | Unverified: Single-connection SQLite default query order follows primary key insertion order, but explicit relationship ordering is absent |

## Defects not fixed

List every defect from the inventory that remains unfixed.

1. **Defect #1 — Idempotent retry casing and whitespace mismatch**:
   - *Short description*: Retrying checkout with differing letter case or surrounding whitespace in `Idempotency-Key` fails to match existing order and returns HTTP 400.
   - *Why it remains unfixed*: This task was strictly an audit-and-documentation task. No source code modifications or bug fixes were performed.
   - *Follow-up work*: Needs implementation in `app/utils/idempotency.py`, `app/services/order_service.py`, and `app/dependencies.py`.

2. **Defect #2 — Blank Idempotency-Key header accepted**:
   - *Short description*: Whitespace-only keys (e.g. `"   "`) pass header validation with HTTP 200 instead of being rejected with HTTP 400.
   - *Why it remains unfixed*: This task was strictly an audit-and-documentation task. No source code modifications or bug fixes were performed.
   - *Follow-up work*: Needs implementation in `app/dependencies.py`.

3. **Defect #3 — PAYMENT_DECLINE_TOKEN configuration ignored**:
   - *Short description*: Configurable payment decline token environment variable is ignored; service hardcodes `"decline"`.
   - *Why it remains unfixed*: This task was strictly an audit-and-documentation task. No source code modifications or bug fixes were performed.
   - *Follow-up work*: Needs implementation in `app/services/payment.py`.

4. **Defect #4 — GET /products 307 Temporary Redirect**:
   - *Short description*: Requesting `GET /products` returns a 307 redirect rather than 200 OK with catalogue.
   - *Why it remains unfixed*: This task was strictly an audit-and-documentation task. No source code modifications or bug fixes were performed.
   - *Follow-up work*: Needs implementation in `app/api/products.py`.

5. **Defect #5 — Discount code whitespace ignored**:
   - *Short description*: Discount codes with leading or trailing whitespace evaluate to 0 discount.
   - *Why it remains unfixed*: This task was strictly an audit-and-documentation task. No source code modifications or bug fixes were performed.
   - *Follow-up work*: Needs implementation in `app/services/pricing.py`.

6. **Defect #6 — Missing pythonpath in pyproject.toml**:
   - *Short description*: Invoking `pytest` directly from root fails during collection with `ModuleNotFoundError: No module named 'app'`.
   - *Why it remains unfixed*: This task was strictly an audit-and-documentation task. No source code modifications or bug fixes were performed.
   - *Follow-up work*: Needs configuration addition in `pyproject.toml`.

## Verification

Commands run:

```bash
.\.venv\Scripts\pytest
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

======================== 28 passed, 1 warning in 3.20s ========================
```

Before/after reproduction for each fixed defect:

Because no fixes were implemented during this audit, no after-fix verification was performed in this task. Pre-fix reproduction evidence collected during the audit for each confirmed defect is recorded below:

1. **Defect 1 (Idempotent retry with differing case/whitespace)**:
   - *Pre-fix reproduction*: `POST /checkout` with `Idempotency-Key: "my-lower-key"` succeeded with HTTP 200. Replaying with `Idempotency-Key: "MY-LOWER-KEY"` or `"  key-with-space  "` returned HTTP 400 `{"detail":"Cart is empty"}` because `find_order` failed to match the key and the cart was already emptied.

2. **Defect 2 (Blank Idempotency-Key)**:
   - *Pre-fix reproduction*: `POST /checkout` with `Idempotency-Key: "   "` succeeded with HTTP 200 because `not idempotency_key` evaluated to False and length was $\le 120$.

3. **Defect 3 (Configurable decline token)**:
   - *Pre-fix reproduction*: With `PAYMENT_DECLINE_TOKEN=custom_decline`, `POST /checkout` with `payment_token="custom_decline"` returned HTTP 200 (payment succeeded), while `"decline"` returned HTTP 402.

4. **Defect 4 (GET /products routing)**:
   - *Pre-fix reproduction*: `client.get("/products", follow_redirects=False)` returned HTTP 307 Temporary Redirect to `/products/` instead of returning the catalogue.

5. **Defect 5 (Discount code whitespace)**:
   - *Pre-fix reproduction*: `POST /checkout` with `discount_code="  welcome10  "` returned `discount_minor: 0` because `.upper()` was evaluated without stripping whitespace.

6. **Defect 6 (Direct pytest execution)**:
   - *Pre-fix reproduction*: Running `pytest` directly from root failed with `ModuleNotFoundError: No module named 'app'` due to lack of `pythonpath = ["."]` in `pyproject.toml`.

## Checklist

- [x] I have read `docs/requirements.md` and `docs/submission.md`
- [x] No changes to `tests/` or `docs/requirements.md`
- [ ] A clean checkout runs using the steps in the README
- [ ] Retry and decline behavior matches `docs/requirements.md`
- [x] Every item in the bug inventory is fixed or listed under "Defects not fixed"
- [x] No database files, secrets, or generated artifacts are committed
- [x] I understand this PR is evaluated once, when opened, and will not be merged
