# Incident #047: A checkout that would not stay still

On 2026-10-24, Support reported that a customer saw two confirmation emails after retrying checkout. The first request had timed out at the edge, while the customer repeated it with the same `Idempotency-Key`. Inventory for the mug was reduced twice in one report. The issue could not be reproduced with every client or every payment token.

The storefront team confirmed that the normal cart, product, payment-decline, and order lookup paths were healthy. The incident was mitigated by pausing automatic checkout retries while the team collected request IDs and database snapshots.

## What we know

- The affected route is `POST /checkout`.
- Repeated requests used the same key, but not always the same casing or whitespace.
- A retry sometimes returned a different order representation than the initial response.
- There was no evidence of a payment provider outage.

This document records observations, not a root-cause analysis.

The request archive is retained in the incident fixture folder.
