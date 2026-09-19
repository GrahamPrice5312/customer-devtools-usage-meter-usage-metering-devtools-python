from customer_meter.metering_ledger import EventKind, MeteringLedger, UsageEvent


def main() -> None:
    ledger = MeteringLedger()
    customer_id = "acme-devtools"
    events = [
        UsageEvent(event_id="build-1042", kind=EventKind.BUILD, units=18),
        UsageEvent(event_id="release-77", kind=EventKind.RELEASE, units=5),
        UsageEvent(event_id="build-1042", kind=EventKind.BUILD, units=18),
    ]
    for event in events:
        result = ledger.record(customer_id, event)
        print(result.model_dump(mode="json"))
    print(ledger.usage(customer_id).model_dump(mode="json"))


if __name__ == "__main__":
    main()
