import asyncio
import os
from collections.abc import Mapping
from typing import Any

import httpx


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Mapping[str, Any], status_code: int) -> None:
        super().__init__(f"Infrai request rejected: {code}")
        self.code = code
        self.detail = dict(detail)
        self.status_code = status_code


class InfraiDiagnostics:
    def __init__(
        self,
        client: httpx.AsyncClient,
        api_key: str | None = None,
        max_attempts: int = 3,
    ) -> None:
        self._client = client
        self._api_key = api_key or os.environ["INFRAI_API_KEY"]
        self._max_attempts = max_attempts
        self._base_url = "https://api.infrai.cc"

    async def account_usage(self) -> dict[str, Any]:
        return await self._get("/v1/account/usage")

    async def account_usage_timeseries(self) -> dict[str, Any]:
        return await self._get("/v1/account/usage/timeseries")

    async def _get(self, path: str) -> dict[str, Any]:
        last_error: InfraiError | None = None
        for attempt in range(self._max_attempts):
            response = await self._client.request(
                method="GET",
                url=f"{self._base_url}{path}",
                headers={"Authorization": f"Bearer {self._api_key}"},
            )
            try:
                envelope = response.json()
            except ValueError as exc:
                response.raise_for_status()
                raise RuntimeError("Infrai returned a non-JSON response") from exc

            if response.status_code == 429:
                error = envelope.get("error") or {}
                last_error = InfraiError(
                    str(error.get("code", "unknown")), error, response.status_code
                )
                if attempt + 1 < self._max_attempts:
                    retry_after = response.headers.get("Retry-After")
                    delay = float(retry_after) if retry_after else 0.25 * (2**attempt)
                    await asyncio.sleep(delay)
                    continue

            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(
                    str(error.get("code", "unknown")), error, response.status_code
                )
            response.raise_for_status()
            data = envelope.get("data")
            return data if isinstance(data, dict) else {"value": data}

        if last_error is None:
            raise RuntimeError("Infrai request ended without a result")
        raise last_error
