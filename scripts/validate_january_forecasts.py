
import json
import sys
from collections import defaultdict
from datetime import UTC, date, datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from app.analytics import select_forecasts_as_of


FORECAST_FILE = PROJECT_ROOT / "data" / "raw" / "windfor-2026-01.json"

UK_TIMEZONE = ZoneInfo("Europe/London")
UTC_TIMEZONE = UTC


def load_forecasts() -> list[dict]:
    with FORECAST_FILE.open(encoding="utf-8") as file:
        return json.load(file)


def parse_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(
        value.replace("Z", "+00:00")
    ).astimezone(UTC_TIMEZONE)


def main() -> None:
    records = load_forecasts()

    print("January 2026 Forecast Availability Validation")
    print("=" * 65)
    print(f"Total forecast records: {len(records)}")

    total_expected = 31 * 24
    total_available = 0
    incomplete_dates = 0
    selection_mismatches = 0

    for day_number in range(1, 32):
        delivery_date = date(2026, 1, day_number)

        cutoff_local = datetime.combine(
            delivery_date - timedelta(days=1),
            time(16, 0),
            tzinfo=UK_TIMEZONE,
        )
        cutoff_utc = cutoff_local.astimezone(UTC_TIMEZONE)

        delivery_start = datetime.combine(
            delivery_date,
            time.min,
            tzinfo=UTC_TIMEZONE,
        )
        delivery_end = delivery_start + timedelta(days=1)

        selected = select_forecasts_as_of(records, cutoff_utc)

        daily = selected[
            (selected["delivery_time"] >= pd.Timestamp(delivery_start))
            & (selected["delivery_time"] < pd.Timestamp(delivery_end))
        ]

        # Independently determine the latest eligible source record
        # for every delivery hour on this date.
        eligible_by_delivery = {}

        for record in records:
            delivery_time = parse_timestamp(record["startTime"])
            publish_time = parse_timestamp(record["publishTime"])

            if (
                delivery_start <= delivery_time < delivery_end
                and publish_time <= cutoff_utc
            ):
                current = eligible_by_delivery.get(delivery_time)

                if current is None or publish_time > current["publish_time"]:
                    eligible_by_delivery[delivery_time] = {
                        "publish_time": publish_time,
                        "generation": float(record["generation"]),
                    }

        expected_timestamps = {
            delivery_start + timedelta(hours=hour)
            for hour in range(24)
        }

        selected_timestamps = set(daily["delivery_time"])
        missing = sorted(expected_timestamps - selected_timestamps)

        date_mismatches = 0

        for _, row in daily.iterrows():
            expected = eligible_by_delivery.get(
                row["delivery_time"].to_pydatetime()
            )

            if (
                expected is None
                or float(row["forecast_mw"]) != expected["generation"]
            ):
                date_mismatches += 1

        selection_mismatches += date_mismatches
        available_hours = len(daily)
        total_available += available_hours

        status = (
            "OK"
            if available_hours == 24
            and not missing
            and date_mismatches == 0
            else "INCOMPLETE"
        )

        print(
            f"{delivery_date}: "
            f"{available_hours:2}/24 hours | "
            f"cutoff {cutoff_utc.isoformat()} | "
            f"selection mismatches: {date_mismatches} | "
            f"{status}"
        )

        if missing:
            incomplete_dates += 1
            print("  Missing hours:")
            for timestamp in missing:
                print(f"    {timestamp.isoformat()}")

        if date_mismatches:
            incomplete_dates += 1

    print("\nOverall summary")
    print("=" * 65)
    print(f"Expected forecast hours: {total_expected}")
    print(f"Available forecast hours: {total_available}")
    print(f"Missing forecast hours: {total_expected - total_available}")
    print(f"Selection mismatches: {selection_mismatches}")
    print(f"Dates with incomplete coverage: {incomplete_dates}")


if __name__ == "__main__":
    main()
