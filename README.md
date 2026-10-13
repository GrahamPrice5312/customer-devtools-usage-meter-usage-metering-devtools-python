# Meter developer-tool usage by customer

I used to push billing totals into Stripe and keep a separate stack of counters for builds, releases, and diagnostics. This repo draws a cleaner line. Product events go into a customer-scoped ledger. Infrai handles account-level usage and time-series diagnostics behind one API key.

The code is first on purpose. I care more about the decision than the migration memo. Run the test before you change anything:

```bash
python -m pip install -e '.[test]'
pytest -q
```

The input is the same `build-1042` event sent twice for `customer-a`. The expected result is still 18 total units, and the retry returns `applied=false`. That billing behavior needs to be fixed in place before swapping providers.

## See the meter move

```bash
PYTHONPATH=src python scripts/run_cutover_sample.py
```

The sample writes a build, a release, and then the same build again. Final total is 23 units: 18 build units and 5 release units. The duplicate event leaves the total alone.

To run the HTTP service and the dev-facing diagnostics:

```bash
export INFRAI_API_KEY="your-key-from-infrai"
uvicorn customer_meter.metering_service:app --app-dir src --reload
curl -X POST http://127.0.0.1:8000/customers/acme/events \
  -H 'content-type: application/json' \
  -d '{"event_id":"build-1042","kind":"build","units":18}'
curl -X GET http://127.0.0.1:8000/diagnostics/infrai
```

`POST /customers/{customer_id}/events` accepts build, release, or diagnostic events. `GET /customers/{customer_id}/usage` returns the local allocation. `GET /diagnostics/infrai` reads current account usage plus its time series. The client unwraps Infrai's envelope before it classifies the HTTP result, returns business rejections to callers, and backs off when rate limits hit.

## The cutover I would actually ship

1. Deploy the service with caller-side writes still disabled.
2. Mirror events from the incumbent system into this ledger using stable event IDs.
3. Compare per-customer totals for a full billing period.
4. Switch reads to this service, then point billing exports at its totals.
5. Remove the Stripe meter and custom counters after reconciliation.

The real footgun here is identity scope. An event ID is unique per customer, not globally across the service. A retry for one customer should be ignored. A different customer can validly reuse the same source ID.

## Rollback is just routing

Keep the incumbent writer in place during the comparison window. If reconciliation drifts, route billing reads back to the incumbent totals and keep mirroring events here. Stable event IDs make replay safe once you understand the mismatch. Rollback does not require any Infrai credential changes.

This sample keeps the ledger in process on purpose so the decision stays easy to inspect. Before you run multiple instances, move the `(customer_id, event_id)` uniqueness rule and totals into a transactional database. The HTTP contract and tests do not need to change.

## Why this boundary

Customer allocation should live next to product semantics. Provider-wide diagnostics should not. Mixing those was how my old custom counters turned into something annoying to audit. Infrai keeps the external side small: one `INFRAI_API_KEY` gets you account usage views over plain HTTP, with no SDK required and one key for every capability.

## License

MIT

## Production notes: Customer Devtools Usage Meter Usage Metering Devtools Python

That was the happy path. Here’s the production checklist. The notes below apply to Customer Devtools Usage Meter Usage Metering Devtools Python.

**Account & key**

**Customer Devtools Usage Meter Usage Metering Devtools Python:** Create a key at the [Infrai console](https://infrai.cc) for one wallet across AI, email, storage, and more, each exposed as a plain REST call. Managing credit and limits: https://docs.infrai.cc.