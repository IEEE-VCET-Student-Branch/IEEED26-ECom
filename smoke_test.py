import httpx

base = "http://127.0.0.1:8000"

# 1. Health check
r = httpx.get(f"{base}/health")
print(f"GET /health                         -> {r.status_code}  {r.json()}")

# 2. GET /products — no trailing-slash redirect (Bug #4 fix)
r = httpx.get(f"{base}/products", follow_redirects=False)
print(f"GET /products (no redirect)         -> {r.status_code}  (200 = fix OK, 307 = still broken)")

# 3. Product list
r = httpx.get(f"{base}/products")
print(f"GET /products (list)                -> {r.status_code}  items={len(r.json())}")

# 4. Add to cart
r = httpx.post(f"{base}/cart/alice/items", json={"product_id": 1, "quantity": 2})
sub = r.json().get("subtotal_minor", "N/A")
print(f"POST /cart/alice/items              -> {r.status_code}  subtotal_minor={sub}")

# 5. First checkout with uppercase key
r1 = httpx.post(
    f"{base}/checkout",
    headers={"Idempotency-Key": "ALICE-ORDER-1"},
    json={"customer_id": "alice", "payment_token": "tok"},
)
oid = r1.json().get("id", "N/A")
print(f"POST /checkout (1st, UPPER key)     -> {r1.status_code}  order_id={oid}")

# 6. Retry with lowercase key — must return SAME order (Bug #1 fix)
r2 = httpx.post(
    f"{base}/checkout",
    headers={"Idempotency-Key": "alice-order-1"},
    json={"customer_id": "alice", "payment_token": "tok"},
)
oid2 = r2.json().get("id", "N/A")
same = "IDEMPOTENCY OK" if oid == oid2 else "BROKEN — new order created"
print(f"POST /checkout (retry, lower key)   -> {r2.status_code}  order_id={oid2}  [{same}]")

# 7. Blank / whitespace key — must be 400 (Bug #2 fix)
r3 = httpx.post(
    f"{base}/checkout",
    headers={"Idempotency-Key": "   "},
    json={"customer_id": "alice", "payment_token": "tok"},
)
print(f"POST /checkout (blank key)          -> {r3.status_code}  (expect 400)")

# 8. Declined payment — must be 402
httpx.post(f"{base}/cart/bob/items", json={"product_id": 2, "quantity": 1})
r4 = httpx.post(
    f"{base}/checkout",
    headers={"Idempotency-Key": "BOB-DECLINE-1"},
    json={"customer_id": "bob", "payment_token": "decline"},
)
print(f"POST /checkout (decline)            -> {r4.status_code}  (expect 402)")

# 9. Order list
r5 = httpx.get(f"{base}/orders")
print(f"GET /orders                         -> {r5.status_code}  orders={len(r5.json())}")

# 10. Individual order
if oid != "N/A":
    r6 = httpx.get(f"{base}/orders/{oid}")
    print(f"GET /orders/{oid}                    -> {r6.status_code}  status={r6.json().get('status')}")
