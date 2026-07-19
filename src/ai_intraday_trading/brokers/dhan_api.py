from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib import error, request

from ai_intraday_trading.config import DhanApiConfig


class DhanApiError(RuntimeError):
    """Raised when Dhan API returns an error or invalid configuration."""


@dataclass(slots=True)
class DhanApiClient:
    config: DhanApiConfig

    def get_fund_limits(self) -> dict[str, Any]:
        return self._get_json("/fundlimit")

    def get_holdings(self) -> list[dict[str, Any]]:
        payload = self._get_json("/holdings")
        if not isinstance(payload, list):
            raise DhanApiError("Unexpected holdings response shape.")
        return payload

    def get_positions(self) -> list[dict[str, Any]]:
        payload = self._get_json("/positions")
        if not isinstance(payload, list):
            raise DhanApiError("Unexpected positions response shape.")
        return payload

    def _get_json(self, path: str) -> Any:
        if not self.config.access_token:
            raise DhanApiError("DHAN_ACCESS_TOKEN is missing.")

        url = f"{self.config.base_url}{path}"
        http_request = request.Request(
            url,
            method="GET",
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "access-token": self.config.access_token,
            },
        )

        try:
            with request.urlopen(http_request, timeout=30) as response:
                charset = response.headers.get_content_charset() or "utf-8"
                return json.loads(response.read().decode(charset))
        except error.HTTPError as exc:
            details = exc.read().decode("utf-8", errors="replace")
            raise DhanApiError(f"Dhan API HTTP {exc.code}: {details}") from exc
        except error.URLError as exc:
            raise DhanApiError(f"Unable to reach Dhan API: {exc.reason}") from exc
