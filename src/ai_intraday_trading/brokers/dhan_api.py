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

    def calculate_margin(self, payload: dict[str, Any]) -> dict[str, Any]:
        response = self._post_json("/margincalculator", payload)
        if not isinstance(response, dict):
            raise DhanApiError("Unexpected margin calculator response shape.")
        return response

    def place_super_order(
        self,
        payload: dict[str, Any],
        *,
        confirmation_phrase: str,
    ) -> dict[str, Any]:
        if not self.config.live_orders_enabled:
            raise DhanApiError("Live orders are disabled by configuration.")
        correlation_id = str(payload.get("correlationId", ""))
        if confirmation_phrase != f"PLACE {correlation_id}":
            raise DhanApiError("Exact action-time confirmation phrase is required.")
        response = self._post_json("/super/orders", payload)
        if not isinstance(response, dict):
            raise DhanApiError("Unexpected super order response shape.")
        return response

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

    def _post_json(self, path: str, payload: dict[str, Any]) -> Any:
        if not self.config.access_token:
            raise DhanApiError("DHAN_ACCESS_TOKEN is missing.")
        if not self.config.client_id:
            raise DhanApiError("DHAN_CLIENT_ID is missing.")

        url = f"{self.config.base_url}{path}"
        body = dict(payload)
        body.setdefault("dhanClientId", self.config.client_id)
        http_request = request.Request(
            url,
            data=json.dumps(body).encode("utf-8"),
            method="POST",
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
