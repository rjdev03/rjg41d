
import pandas as pd
import pytest

from app.analytics import (
    aggregate_actuals_hourly,
    calculate_errors,
    calculate_metrics,
    select_forecasts_as_of,
)


def test_aggregate_actuals_hourly_averages_two_readings():
    records = [
        {"startTime": "2026-01-14T10:00:00Z", "generation": 100},
        {"startTime": "2026-01-14T10:30:00Z", "generation": 120},
        {"startTime": "2026-01-14T11:00:00Z", "generation": 140},
        {"startTime": "2026-01-14T11:30:00Z", "generation": 160},
    ]

    result = aggregate_actuals_hourly(records)

    assert len(result) == 2
    assert result["actual_mw"].tolist() == [110, 150]
    assert result["delivery_time"].tolist() == [
        pd.Timestamp("2026-01-14T10:00:00Z"),
        pd.Timestamp("2026-01-14T11:00:00Z"),
    ]


def test_aggregate_actuals_hourly_excludes_incomplete_hours():
    records = [
        {"startTime": "2026-01-14T10:00:00Z", "generation": 100},
        {"startTime": "2026-01-14T10:30:00Z", "generation": 120},
        {"startTime": "2026-01-14T11:00:00Z", "generation": 140},
    ]

    result = aggregate_actuals_hourly(records)

    assert len(result) == 1
    assert result.iloc[0]["actual_mw"] == 110


def test_aggregate_actuals_hourly_rejects_duplicate_timestamps():
    records = [
        {"startTime": "2026-01-14T10:00:00Z", "generation": 100},
        {"startTime": "2026-01-14T10:00:00Z", "generation": 120},
    ]

    with pytest.raises(
        ValueError,
        match="Duplicate actual-generation timestamps",
    ):
        aggregate_actuals_hourly(records)


def test_select_forecasts_as_of_uses_latest_eligible_version():
    records = [
        {
            "publishTime": "2026-01-14T08:00:00Z",
            "startTime": "2026-01-15T10:00:00Z",
            "generation": 100,
        },
        {
            "publishTime": "2026-01-14T09:00:00Z",
            "startTime": "2026-01-15T10:00:00Z",
            "generation": 120,
        },
        {
            "publishTime": "2026-01-14T10:00:00Z",
            "startTime": "2026-01-15T10:00:00Z",
            "generation": 999,
        },
    ]

    cutoff = pd.Timestamp("2026-01-14T09:30:00Z").to_pydatetime()

    result = select_forecasts_as_of(records, cutoff)

    assert len(result) == 1
    assert result.iloc[0]["forecast_mw"] == 120
    assert result.iloc[0]["delivery_time"] == pd.Timestamp(
        "2026-01-15T10:00:00Z"
    )


def test_select_forecasts_as_of_rejects_naive_cutoff():
    records = [
        {
            "publishTime": "2026-01-14T08:00:00Z",
            "startTime": "2026-01-15T10:00:00Z",
            "generation": 100,
        },
    ]

    cutoff = pd.Timestamp("2026-01-14T09:30:00").to_pydatetime()

    with pytest.raises(ValueError, match="cutoff must include a timezone"):
        select_forecasts_as_of(records, cutoff)


def test_calculate_errors_aligns_matching_hours():
    forecasts = pd.DataFrame({
        "delivery_time": pd.to_datetime(
            ["2026-01-14T10:00:00Z", "2026-01-14T11:00:00Z"],
            utc=True,
        ),
        "forecast_mw": [120, 140],
    })

    actuals = pd.DataFrame({
        "delivery_time": pd.to_datetime(
            ["2026-01-14T10:00:00Z", "2026-01-14T11:00:00Z"],
            utc=True,
        ),
        "actual_mw": [100, 160],
    })

    result = calculate_errors(forecasts, actuals)

    assert result["error_mw"].tolist() == [20, -20]


def test_calculate_metrics_returns_expected_values():
    errors = pd.DataFrame({"error_mw": [20, -20]})

    result = calculate_metrics(errors)

    assert result["observation_count"] == 2
    assert result["mae_mw"] == pytest.approx(20)
    assert result["rmse_mw"] == pytest.approx(20)
    assert result["bias_mw"] == pytest.approx(0)


def test_calculate_metrics_handles_no_observations():
    errors = pd.DataFrame({"error_mw": []})

    result = calculate_metrics(errors)

    assert result == {
        "observation_count": 0,
        "mae_mw": None,
        "rmse_mw": None,
        "bias_mw": None,
    }


def test_aggregate_actuals_hourly_excludes_irregular_hours():
    records = [
        {
            "startTime": "2026-01-14T10:00:00Z",
            "generation": 100,
        },
        {
            "startTime": "2026-01-14T10:15:00Z",
            "generation": 120,
        },
        {
            "startTime": "2026-01-14T11:00:00Z",
            "generation": 140,
        },
        {
            "startTime": "2026-01-14T11:30:00Z",
            "generation": 160,
        },
    ]

    result = aggregate_actuals_hourly(records)

    assert len(result) == 1
    assert result.iloc[0]["actual_mw"] == 150
