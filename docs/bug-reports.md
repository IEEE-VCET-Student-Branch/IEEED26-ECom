# Checkout reports

## BR-882

Customer `mira` checked out a coffee and received a gateway timeout. Retrying with the original key produced two order IDs in the client log. The warehouse saw one shipment at first and a second reservation several minutes later.

## BR-889

Customer `jon` retried a declined payment after changing the payment token. No order was created for the declined attempt. A later successful checkout behaved normally.

## BR-894

Support could not reproduce a duplicate using the API console. Their console copied the idempotency header exactly, while the mobile client trimmed and reassembled headers.

All three reports were filed against release 1.0.0.
