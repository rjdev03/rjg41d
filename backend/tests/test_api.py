
import json
from pathlib import Path

from fastapi.testclient import TestClient

from app import main

client = TestClient(main.app)


def test_wind_analytics_returns_expected_response(
    tmp_path: Path,
    monkeypatch,
):
    # Arrange: create temporary consolidated dataset files.
    actual_records = [
        {
            "fuelType": "WIND",
            "startTime": "2026-01-15T00:00:00Z",
            "generation": 100,
        },
        {
            "fuelType": "WIND",
            "startTime": "2026-01-15T00:30:00Z",
            "generation": 120,
        },
    ]

    forecast_records = [
        {
            "publishTime": "2026-01-14T15:30:00Z",
            "startTime": "2026-01-15T00:00:00Z",
            "generation": 130,
        },
        {
            "publishTime": "2026-01-14T18:30:00Z",
            "startTime": "2026-01-15T00:00:00Z",
            "generation": 150,
        },
    ]

    actual_file = tmp_path / "fuelhh-wind-2026-01.json"
    forecast_file = tmp_path / "windfor-2026-01.json"

    actual_file.write_text(json.dumps(actual_records))
    forecast_file.write_text(json.dumps(forecast_records))

    # Temporarily redirect the API to the test datasets.
    monkeypatch.setattr(main, "ACTUAL_FILE", actual_file)
    monkeypatch.setattr(main, "FORECAST_FILE", forecast_file)

    # Act: request the analytics endpoint.
    response = client.get(
        "/api/analytics/wind",
        params={"delivery_date": "2026-01-15"},
    )

    # Assert: verify the response.
    assert response.status_code == 200

    data = response.json()

    assert data["delivery_date"] == "2026-01-15"
    assert data["decision_cutoff"] == "2026-01-14T16:00:00+00:00"

    assert data["coverage"]["expected_hours"] == 24
    assert data["coverage"]["forecast_hours_available"] == 1
    assert data["coverage"]["actual_hours_available"] == 1
    assert data["coverage"]["evaluated_hours"] == 1
    assert data["coverage"]["missing_forecast_hours"] == 23
    assert data["coverage"]["missing_actual_hours"] == 23

    assert data["metrics"]["observation_count"] == 1
    assert data["metrics"]["mae_mw"] == 20.0
    assert data["metrics"]["rmse_mw"] == 20.0
    assert data["metrics"]["bias_mw"] == 20.0

    assert len(data["hourly_data"]) == 1

    # The 18:30 forecast was published after the cutoff.
    # Therefore, the 15:30 forecast (130 MW) must be selected.
    assert data["hourly_data"][0]["forecast_mw"] == 130.0
    assert data["hourly_data"][0]["actual_mw"] == 110.0


def test_availability_returns_supported_delivery_dates(
    tmp_path: Path,
    monkeypatch,
):
    actual_records = [
        {
            "fuelType": "WIND",
            "startTime": "2026-01-15T00:00:00Z",
            "generation": 100,
        },
        {
            "fuelType": "WIND",
            "startTime": "2026-01-15T00:30:00Z",
            "generation": 120,
        },
    ]

    forecast_records = [
        {
            "publishTime": "2026-01-14T15:30:00Z",
            "startTime": "2026-01-15T00:00:00Z",
            "generation": 130,
        },
        {
            "publishTime": "2026-01-14T18:30:00Z",
            "startTime": "2026-01-15T00:00:00Z",
            "generation": 150,
        },
    ]

    actual_file = tmp_path / "fuelhh-wind-2026-01.json"
    forecast_file = tmp_path / "windfor-2026-01.json"

    actual_file.write_text(json.dumps(actual_records))
    forecast_file.write_text(json.dumps(forecast_records))

    monkeypatch.setattr(main, "ACTUAL_FILE", actual_file)
    monkeypatch.setattr(main, "FORECAST_FILE", forecast_file)

    response = client.get("/api/analytics/availability")

    assert response.status_code == 200

    data = response.json()
    assert len(data["available_dates"]) == 1

    available = data["available_dates"][0]

    assert available["delivery_date"] == "2026-01-15"
    assert available["actual_hours_available"] == 1
    assert available["forecast_hours_available"] == 1
    assert available["evaluated_hours"] == 1
