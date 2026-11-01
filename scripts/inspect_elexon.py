import json
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path


def parse_time(value: str) -> datetime:
    """Convert an ISO timestamp, including trailing Z, into a datetime."""
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def inspect_file(filename: str) -> None:
    path = Path(filename)

    print(f"\n{'=' * 65}")
    print(f"File: {path}")
    print("=" * 65)

    with path.open(encoding="utf-8") as file:
        records = json.load(file)

    if not isinstance(records, list) or not records:
        print("ERROR: Expected a non-empty JSON array.")
        return

    print(f"Total records: {len(records)}")
    print(f"Fields: {', '.join(sorted(records[0].keys()))}")

    # Publication timestamps tell us when records became available.
    publication_times = [
        parse_time(r["publishTime"])
        for r in records
        if r.get("publishTime")
    ]

    if publication_times:
        print(f"Distinct publication times: {len(set(publication_times))}")
        print(f"First publication: {min(publication_times).isoformat()}")
        print(f"Last publication:  {max(publication_times).isoformat()}")

    # Delivery timestamps tell us which periods the records describe.
    delivery_times = [
        parse_time(r["startTime"])
        for r in records
        if r.get("startTime")
    ]

    counts = Counter(delivery_times)
    unique_times = sorted(counts)

    print(f"Unique delivery start times: {len(unique_times)}")
    if unique_times:
        print(f"First delivery start: {unique_times[0].isoformat()}")
        print(f"Last delivery start:  {unique_times[-1].isoformat()}")

    duplicates = sum(count - 1 for count in counts.values())
    print(f"Repeated delivery timestamps: {duplicates}")

    # Show the time intervals between consecutive delivery timestamps.
    intervals = Counter(
        int((later - earlier).total_seconds() / 60)
        for earlier, later in zip(unique_times, unique_times[1:])
    )
    print(f"Intervals between delivery timestamps (minutes): {dict(sorted(intervals.items()))}")

    # Show how many forecast records belong to each publication.
    publication_counts = Counter(
        r["publishTime"] for r in records if r.get("publishTime")
    )
    print(f"Records per publication (first 10): {publication_counts.most_common(10)}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/inspect_elexon.py FILE [FILE ...]")
        sys.exit(1)

    for filename in sys.argv[1:]:
        try:
            inspect_file(filename)
        except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
            print(f"\nERROR inspecting {filename}: {error}")
