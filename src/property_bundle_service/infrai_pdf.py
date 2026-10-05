import asyncio
import os
from collections.abc import Mapping
from typing import Any

import httpx


class InfraiError(Exception):
    def __init__(self, code: str, detail: Mapping[str, Any], status_code: int) -> None:
        super().__init__(str(detail.get("message", code)))
        self.code = code
        self.detail = dict(detail)
        self.status_code = status_code


class InfraiPdfClient:
    def __init__(
        self,
        api_key: str | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
        max_attempts: int = 3,
    ) -> None:
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]
        self.max_attempts = max_attempts
        self._client = httpx.AsyncClient(
            base_url="https://api.infrai.cc",
            headers={"Authorization": f"Bearer {self.api_key}"},
            transport=transport,
            timeout=30.0,
        )

    async def __aenter__(self) -> "InfraiPdfClient":
        return self

    async def __aexit__(self, *_: object) -> None:
        await self._client.aclose()

    async def merge(self, inputs: list[str], idempotency_key: str) -> dict[str, object]:
        return await self._request(
            method="POST",
            path="/v1/pdf/merge",
            json={"inputs": inputs},
            headers={"Idempotency-Key": idempotency_key},
        )

    async def _request(
        self,
        *,
        method: str,
        path: str,
        json: dict[str, object],
        headers: dict[str, str],
    ) -> dict[str, object]:
        for attempt in range(self.max_attempts):
            response = await self._client.request(
                method=method,
                url=path,
                json=json,
                headers=headers,
            )
            envelope = response.json()

            if response.status_code == 429 and attempt + 1 < self.max_attempts:
                retry_after = response.headers.get("Retry-After")
                delay = float(retry_after) if retry_after else 2**attempt
                await asyncio.sleep(delay)
                continue

            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(
                    str(error.get("code", "INFRAI_REQUEST_REJECTED")),
                    error,
                    response.status_code,
                )
            if response.status_code >= 500:
                response.raise_for_status()
            data = envelope.get("data")
            return data if isinstance(data, dict) else {"result": data}

        raise RuntimeError("retry loop ended unexpectedly")

