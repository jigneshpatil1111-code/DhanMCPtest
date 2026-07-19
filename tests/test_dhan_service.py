from __future__ import annotations

import unittest

from ai_intraday_trading.brokers.dhan_api import DhanApiClient
from ai_intraday_trading.config import DhanApiConfig
from ai_intraday_trading.services.dhan_service import DhanService


class _FakeDhanClient(DhanApiClient):
    def __init__(self) -> None:
        super().__init__(DhanApiConfig(access_token="test", client_id="123"))

    def get_fund_limits(self) -> dict[str, object]:
        return {
            "dhanClientId": "123",
            "availabelBalance": 50000.0,
            "withdrawableBalance": 48000.0,
            "utilizedAmount": 2000.0,
            "collateralAmount": 0.0,
        }


class DhanServiceTests(unittest.TestCase):
    def test_get_fund_summary_maps_expected_fields(self) -> None:
        service = DhanService(_FakeDhanClient())
        summary = service.get_fund_summary()

        self.assertEqual(summary["dhanClientId"], "123")
        self.assertEqual(summary["availableBalance"], 50000.0)
        self.assertEqual(summary["withdrawableBalance"], 48000.0)


if __name__ == "__main__":
    unittest.main()
