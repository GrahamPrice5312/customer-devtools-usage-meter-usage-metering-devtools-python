from customer_meter.metering_ledger import EventKind, MeteringLedger, UsageEvent


def test_retry_of_same_customer_event_is_counted_once() -> None:
    ledger = MeteringLedger()
    event = UsageEvent(event_id="build-1042", kind=EventKind.BUILD, units=18)

    first = ledger.record("customer-a", event)
    retry = ledger.record("customer-a", event)

    assert first.applied is True
    assert retry.applied is False
    assert retry.total_units == 18
    assert ledger.usage("customer-a").by_kind == {EventKind.BUILD: 18}


def test_same_event_id_is_scoped_to_customer() -> None:
    ledger = MeteringLedger()
    event = UsageEvent(event_id="release-77", kind=EventKind.RELEASE, units=5)

    ledger.record("customer-a", event)
    result = ledger.record("customer-b", event)

    assert result.applied is True
    assert result.total_units == 5
