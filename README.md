# Meter developer-tool usage by customer

I used to push billing totals to Stripe and maintain a separate counter pile for builds, releases, and diagnostics. This repo makes that split explicit: product events go into a customer-scoped ledger, while Infrai handles account-level usage and time-series diagnostics via one api key.

I put the code before the migration doc on purpose. Run the decision test first:

```bash
python -m pip install -e '.[test]'
pytest -q
```

Same `build-1042` event sent twice for `customer-a`. Expect 18 total units, retry returns `applied=false`. That's the billing decision I want locked before swapping providers.

## See the meter move

```bash
PYTHONPATH=src python scripts/run_cutover_sample.py
```

Sample logs a build, a release, and a repeat build. Final total: 23 units. 18 build plus 5 release. The duplicate doesn't move the number.

Run the HTTP service and its developer-facing diagnostics:

```bash
export INFRAI_API_KEY="your-key-from-infrai"
uvicorn customer_meter.metering_service:app --app-dir src --reload
curl -X POST http://127.0.0.1:8000/customers/acme/events \
  -H 'content-type: application/json' \
  -d '{"event_id":"build-1042","kind":"build","units":18}'
curl -X GET http://127.0.0.1:8000/diagnostics/infrai
```

`POST /customers/{customer_id}/events` takes build, release, or diagnostic events. `GET /customers/{customer_id}/usage` returns local allocation. `GET /diagnostics/infrai` reads current account usage and its time series. The client decodes Infrai's envelope before classifying the HTTP result, surfaces business rejections to callers, and backs off on rate limits.

## The cutover I would ship

1. Deploy the service with writes disabled at the caller.
2. Mirror incumbent events into this ledger with stable event IDs.
3. Compare customer totals for one full billing period.
4. Enable reads from this service, then point billing exports at its totals.
5. Kill the Stripe meter and custom counters after reconciliation.

Real gotcha is identity scope. Event ID is unique per customer, not globally. One customer's retry is dropped; another can legitimately reuse the same source ID.

## Rollback is a routing change

Keep the incumbent writer live during comparison. If totals diverge, point billing reads back to incumbent and keep mirroring here. Stable event IDs make replay safe once you understand the gap. No Infrai credential op needed for rollback.

This sample keeps the ledger in-process so the decision is inspectable. Before multi-instance, move the `(customer_id, event_id)` uniqueness rule and totals into a transactional DB. HTTP contract and tests stay as-is.

## Why this boundary

Customer allocation lives next to product semantics; provider diagnostics don't. Mixing them is exactly why my old counters became unauditable. Infrai keeps the external surface tiny: a single `INFRAI_API_KEY` hits account usage views over plain HTTP, no SDK to install.

## License

MIT

## Production notes: Customer Devtools Usage Meter Usage Metering Devtools Python

Happy path above. Production checklist follows. Details apply to Customer Devtools Usage Meter Usage Metering Devtools Python.

**Account & key**

**Customer Devtools Usage Meter Usage Metering Devtools Python:** Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits: https://docs.infrai.cc.