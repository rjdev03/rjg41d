import json
import os
from datetime import UTC, date, datetime, time, timedelta
from pathlib import Path
from typing import Annotated
from zoneinfo import ZoneInfo

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from app.analytics import (
    aggregate_actuals_hourly,
    calculate_errors,
    calculate_metrics,
    inspect_data_availability,
    select_forecasts_as_of,
)

app = FastAPI(
    title="Wind Forecast Analytics API",
    version="0.1.0",
)


cors_origins = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173",
    ).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = Path(
    os.getenv("DATA_DIR", PROJECT_ROOT / "data" / "raw")
)

FORECAST_FILE = DATA_DIR / "windfor-2026-01.json"
ACTUAL_FILE = DATA_DIR / "fuelhh-wind-2026-01.json"

UK_TIMEZONE = ZoneInfo("Europe/London")
UTC_TIMEZONE = UTC

JANUARY_START = date(2026, 1, 1)
FEBRUARY_START = date(2026, 2, 1)


def load_json_records(path: Path) -> list[dict]:
    """Load a JSON file containing a list of records."""

    try:
        with path.open(encoding="utf-8") as file:
            records = json.load(file)

    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"Data file not found: {path.name}",
        )

    except json.JSONDecodeError:
        raise HTTPException(
            status_code=500,
            detail=f"Invalid JSON in data file: {path.name}",
        )

    if not isinstance(records, list):
        raise HTTPException(
            status_code=500,
            detail=f"Expected a JSON array in: {path.name}",
        )

    return records


def validate_delivery_date(delivery_date: date) -> None:
    """Restrict analytics requests to the January 2026 dataset."""

    if not JANUARY_START <= delivery_date < FEBRUARY_START:
        raise HTTPException(
            status_code=404,
            detail="Analytics are available only for January 2026.",
        )


def get_delivery_window(delivery_date: date) -> tuple[datetime, datetime]:
    """Return UTC boundaries for a delivery date."""

    delivery_start = datetime.combine(
        delivery_date,
        time.min,
        tzinfo=UTC_TIMEZONE,
    )

    delivery_end = delivery_start + timedelta(days=1)

    return delivery_start, delivery_end


def get_decision_cutoff(delivery_date: date) -> datetime:
    """Return the previous-day 16:00 UK decision cutoff."""

    previous_day = delivery_date - timedelta(days=1)

    return datetime.combine(
        previous_day,
        time(16, 0),
        tzinfo=UK_TIMEZONE,
    )


def filter_delivery_records(
    records: list[dict],
    delivery_start: datetime,
    delivery_end: datetime,
) -> list[dict]:
    """Filter records by their delivery timestamp."""

    return [
        record
        for record in records
        if delivery_start
        <= datetime.fromisoformat(
            record["startTime"]
        ).astimezone(UTC_TIMEZONE)
        < delivery_end
    ]


def load_january_datasets() -> tuple[list[dict], list[dict]]:
    """Load consolidated January forecast and actual datasets."""

    forecast_records = load_json_records(FORECAST_FILE)
    actual_records = load_json_records(ACTUAL_FILE)

    # Retain this filter as a defensive check.
    actual_records = [
        record
        for record in actual_records
        if record.get("fuelType") == "WIND"
    ]

    return forecast_records, actual_records


@app.get("/api/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/analytics/availability")
def get_analytics_availability() -> dict:
    """Return January delivery dates with evaluable observations."""

    forecast_records, actual_records = load_january_datasets()

    available_dates = []

    for day_number in range(1, 32):
        delivery_date = date(2026, 1, day_number)

        cutoff = get_decision_cutoff(delivery_date)

        delivery_start, delivery_end = get_delivery_window(
            delivery_date
        )

        daily_actuals = filter_delivery_records(
            actual_records,
            delivery_start,
            delivery_end,
        )

        daily_forecasts = filter_delivery_records(
            forecast_records,
            delivery_start,
            delivery_end,
        )

        coverage = inspect_data_availability(
            daily_actuals,
            daily_forecasts,
            cutoff,
        )

        if coverage["evaluated_hours"] == 0:
            continue

        available_dates.append({
            "delivery_date": delivery_date.isoformat(),
            "expected_hours": 24,
            **coverage,
        })

    return {"available_dates": available_dates}


@app.get("/api/analytics/wind")
def get_wind_analytics(
    delivery_date: Annotated[
        date,
        Query(description="Delivery date in YYYY-MM-DD format"),
    ],
) -> dict:
    """Evaluate wind forecast accuracy for a delivery date."""

    validate_delivery_date(delivery_date)

    cutoff = get_decision_cutoff(delivery_date)

    delivery_start, delivery_end = get_delivery_window(
        delivery_date
    )

    forecast_records, actual_records = load_january_datasets()

    daily_actuals = filter_delivery_records(
        actual_records,
        delivery_start,
        delivery_end,
    )

    daily_forecasts = filter_delivery_records(
        forecast_records,
        delivery_start,
        delivery_end,
    )

    actuals = aggregate_actuals_hourly(daily_actuals)

    forecasts = select_forecasts_as_of(
        daily_forecasts,
        cutoff,
    )

    errors = calculate_errors(forecasts, actuals)

    metrics = calculate_metrics(errors)

    hourly_records = errors.to_dict(orient="records")

    hourly_data = [
        {
            "delivery_time": row["delivery_time"].isoformat(),
            "forecast_mw": float(row["forecast_mw"]),
            "actual_mw": float(row["actual_mw"]),
            "error_mw": float(row["error_mw"]),
        }
        for row in hourly_records
    ]

    return {
        "delivery_date": delivery_date.isoformat(),
        "decision_cutoff": cutoff.isoformat(),
        "timezone": "Europe/London",
        "coverage": {
            "expected_hours": 24,
            "forecast_hours_available": len(forecasts),
            "actual_hours_available": len(actuals),
            "evaluated_hours": len(errors),
            "missing_forecast_hours": 24 - len(forecasts),
            "missing_actual_hours": 24 - len(actuals),
        },
        "metrics": metrics,
        "hourly_data": hourly_data,
    }
