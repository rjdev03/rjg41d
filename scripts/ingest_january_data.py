
import json
from collections import Counter
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen


BASE_URL = "https://data.elexon.co.uk/bmrs/api/v1/datasets"
DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"

DELIVERY_START = datetime(2026, 1, 1, tzinfo=UTC)
DELIVERY_END = datetime(2026, 2, 1, tzinfo=UTC)

# Publication windows established through live API testing.
FORECAST_PUBLICATION_START = "2025-12-31T00:00:00Z"
FORECAST_PUBLICATION_END = "2026-01-31T00:00:00Z"

ACTUAL_PUBLICATION_START = "2026-01-01T00:00:00Z"
ACTUAL_PUBLICATION_END = "2026-02-01T00:00:00Z"


def fetch_records(
    dataset: str,
    publication_start: str,
    publication_end: str,
) -> list[dict]:
    """Retrieve records from an Elexon dataset publication window."""

    params = urlencode({
        "publishDateTimeFrom": publication_start,
        "publishDateTimeTo": publication_end,
    })

    url = f"{BASE_URL}/{dataset}/stream?{params}"
    request = Request(
        url,
        headers={"User-Agent": "WindForecastAnalytics/1.0"},
    )

    print(f"Downloading {dataset}...")

    with urlopen(request, timeout=180) as response:
        records = json.load(response)

    if not isinstance(records, list):
        raise ValueError(
            f"Expected a JSON array from {dataset}"
        )

    print(f"Retrieved {len(records)} {dataset} records.")

    return records


def parse_timestamp(value: str) -> datetime:
    """Parse an ISO timestamp and normalise it to UTC."""

    return datetime.fromisoformat(
        value.replace("Z", "+00:00")
    ).astimezone(UTC)


def is_january_delivery(record: dict) -> bool:
    """Check whether a record belongs to January 2026 delivery."""

    delivery_time = parse_timestamp(record["startTime"])

    return DELIVERY_START <= delivery_time < DELIVERY_END


def save_records(filename: str, records: list[dict]) -> Path:
    """Save records as formatted JSON."""

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    path = DATA_DIR / filename

    with path.open("w", encoding="utf-8") as file:
        json.dump(records, file, indent=2)

    return path


def validate_actuals(records: list[dict]) -> None:
    """Check actual half-hourly delivery coverage."""

    timestamps = [
        parse_timestamp(record["startTime"])
        for record in records
    ]

    counts = Counter(timestamps)

    duplicates = [
        timestamp
        for timestamp, count in counts.items()
        if count > 1
    ]

    expected_timestamps = {
        DELIVERY_START + timedelta(minutes=30 * period)
        for period in range(31 * 48)
    }

    actual_timestamps = set(timestamps)

    missing = sorted(expected_timestamps - actual_timestamps)
    unexpected = sorted(actual_timestamps - expected_timestamps)

    print("\nActual-generation validation")
    print(f"Expected half-hour periods: {len(expected_timestamps)}")
    print(f"Available records: {len(records)}")
    print(f"Unique delivery timestamps: {len(actual_timestamps)}")
    print(f"Duplicate delivery timestamps: {len(duplicates)}")
    print(f"Missing delivery periods: {len(missing)}")
    print(f"Unexpected delivery periods: {len(unexpected)}")

    if missing:
        print("First missing periods:")
        for timestamp in missing[:10]:
            print(f"  {timestamp.isoformat()}")

    if duplicates:
        print("Duplicate timestamps:")
        for timestamp in duplicates[:10]:
            print(f"  {timestamp.isoformat()}")

    if unexpected:
        print("Unexpected timestamps:")
        for timestamp in unexpected[:10]:
            print(f"  {timestamp.isoformat()}")


def main() -> None:
    print("January 2026 Wind Data Ingestion")
    print("=" * 45)

    # Retrieve all forecast publication snapshots.
    forecast_records = fetch_records(
        "WINDFOR",
        FORECAST_PUBLICATION_START,
        FORECAST_PUBLICATION_END,
    )

    # Retain only forecasts describing January delivery periods.
    january_forecasts = [
        record
        for record in forecast_records
        if is_january_delivery(record)
    ]

    # Retrieve actual generation records.
    actual_records = fetch_records(
        "FUELHH",
        ACTUAL_PUBLICATION_START,
        ACTUAL_PUBLICATION_END,
    )

    # Retain only national wind generation for January delivery.
    january_actuals = [
        record
        for record in actual_records
        if record.get("fuelType") == "WIND"
        and is_january_delivery(record)
    ]

    # Save both datasets.
    forecast_path = save_records(
        "windfor-2026-01.json",
        january_forecasts,
    )

    actual_path = save_records(
        "fuelhh-wind-2026-01.json",
        january_actuals,
    )

    print("\nIngestion summary")
    print("=" * 45)
    print(f"WINDFOR records saved: {len(january_forecasts)}")
    print(f"FUELHH WIND records saved: {len(january_actuals)}")
    print(
        "WINDFOR publication snapshots:",
        len({
            record["publishTime"]
            for record in january_forecasts
        }),
    )
    print(f"Forecast file: {forecast_path}")
    print(f"Actual file: {actual_path}")

    validate_actuals(january_actuals)

    print("\nIngestion completed.")


if __name__ == "__main__":
    main()
