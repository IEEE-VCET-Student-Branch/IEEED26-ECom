# Behavioral requirements

This document is the contract for Northstar Market. It describes what the running
service must do, in terms a client can observe. It says nothing about how the code
should achieve it.

The tests in `tests/` cover part of this contract. They are a starting point, not a
complete specification: passing them is necessary but not sufficient.

## Money and pricing

- All amounts are integers in minor units. No floating point is exposed.
- `subtotal_minor` is the sum of `unit_price_minor * quantity` for every cart line.
- Discount-code matching is case-insensitive. `WELCOME10` grants 10% of the subtotal,
  rounded down to the nearest minor unit. An absent or unknown code grants `0`.
- `total_minor` is always `subtotal_minor - discount_minor`.
- An order records the SKU, name and unit price of each line at purchase time. Later
  catalogue changes must not alter existing orders.

## Catalogue

- `GET /products` returns the catalogue ordered by product id.
- `GET /products/{id}` returns one product, or `404` when it does not exist.

## Cart

- `GET /cart/{customer_id}` returns the customer's cart, creating an empty one when the
  customer has none.
- `POST /cart/{customer_id}/items` adds a product to the cart. Adding a product that is
  already present increments its quantity rather than creating a second line. Each
  request quantity must be between 1 and 99.
- Adding a product that does not exist returns `404`.
- Reading or changing a cart never reserves inventory.

## Inventory

- Inventory is validated at checkout. If any line exceeds the available inventory,
  checkout fails with `409` and changes nothing.
- A successful checkout decrements inventory by each line's quantity, exactly once per
  order, including when the client retries the same checkout.
- A failed checkout (validation failure, decline, or error) leaves inventory unchanged.

## Payments

- The payment provider is deterministic and offline. It has no external dependencies.
- The token that simulates a decline is read from the `PAYMENT_DECLINE_TOKEN`
  environment setting, which defaults to `decline`. Every other non-empty token
  succeeds.
- A decline returns `402`, creates no order, records no payment attempt, and leaves the
  cart and inventory untouched. The same idempotency key may be reused after a decline.

## Checkout and idempotency

- `POST /checkout` requires an `Idempotency-Key` header. The key must be non-blank and at
  most 120 characters; otherwise the request is rejected with `400`.
- A key identifies one logical checkout. Two requests with the same logical key must
  return the same order and an identical response body, regardless of letter case or
  surrounding whitespace in the header value.
- Replaying a request must not create a second order, decrement inventory again, or
  record another payment attempt.
- Requests with different logical keys are independent and create separate orders.
- A successful checkout clears the customer's cart. A failed checkout leaves it intact.

## Orders

- `GET /orders/{id}` returns the order and its line items, or `404` when it does not
  exist.
- `GET /orders` lists orders in ascending id order.
- A successful checkout produces `status: "paid"`.

## Configuration

- `DATABASE_URL` selects the persistence layer. It defaults to a local SQLite file.
- `PAYMENT_DECLINE_TOKEN` selects the token that simulates a declined payment.
