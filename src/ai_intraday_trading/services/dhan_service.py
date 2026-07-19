from __future__ import annotations

from ai_intraday_trading.brokers.dhan_api import DhanApiClient


class DhanService:
    def __init__(self, client: DhanApiClient) -> None:
        self.client = client

    def get_fund_summary(self) -> dict[str, float | str | None]:
        payload = self.client.get_fund_limits()
        return {
            "dhanClientId": payload.get("dhanClientId"),
            "availableBalance": payload.get("availabelBalance"),
            "withdrawableBalance": payload.get("withdrawableBalance"),
            "utilizedAmount": payload.get("utilizedAmount"),
            "collateralAmount": payload.get("collateralAmount"),
        }
