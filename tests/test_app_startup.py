from ai_intraday_trading.main import create_app


def test_create_app_registers_live_status_route() -> None:
    app = create_app()

    assert "/health" in {route.path for route in app.routes}
    assert "/api/live/status" in {route.path for route in app.routes}
