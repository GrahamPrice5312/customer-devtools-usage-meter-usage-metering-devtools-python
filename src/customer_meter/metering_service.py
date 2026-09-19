from contextlib import asynccontextmanager
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException, Request

from .infrai_diagnostics import InfraiDiagnostics, InfraiError
from .metering_ledger import CustomerUsage, MeterResult, MeteringLedger, UsageEvent


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with httpx.AsyncClient(timeout=10.0) as client:
        app.state.infrai = InfraiDiagnostics(client)
        yield


app = FastAPI(title="Customer developer-tools meter", lifespan=lifespan)
ledger = MeteringLedger()


@app.post("/customers/{customer_id}/events", response_model=MeterResult)
def record_event(customer_id: str, event: UsageEvent) -> MeterResult:
    return ledger.record(customer_id, event)


@app.get("/customers/{customer_id}/usage", response_model=CustomerUsage)
def customer_usage(customer_id: str) -> CustomerUsage:
    return ledger.usage(customer_id)


@app.get("/diagnostics/infrai")
async def infrai_usage(request: Request) -> dict[str, Any]:
    diagnostics: InfraiDiagnostics = request.app.state.infrai
    try:
        return {
            "usage": await diagnostics.account_usage(),
            "timeseries": await diagnostics.account_usage_timeseries(),
        }
    except InfraiError as exc:
        client_status = exc.status_code if 400 <= exc.status_code < 500 else 502
        raise HTTPException(
            status_code=client_status,
            detail={"code": exc.code, "error": exc.detail},
        ) from exc
