# Investigation guide

Start with the behavior, then reduce it to a deterministic request sequence. Compare the database before and after each request. Inspect the checkout call graph and the commits that changed it. `git log --all -- app/services app/api` is a useful first pass, followed by focused diffs.

The incident evidence includes both observations and hypotheses. Treat wording in chat messages as leads rather than facts. A good fix should preserve normal checkout, declines, inventory, pricing, and order retrieval while making a retry stable.

Record both the HTTP response and order count for each attempt.
