from __future__ import annotations

import csv
import json
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path


COMPARISON_PATH = Path(
    "data/processed/trajectory/oem_comparison_detail.csv"
)

EVENTS_PATH = Path(
    "data/reference/trajectory_events.json"
)

OUTPUT_PATH = Path(
    "data/processed/trajectory/event_window_analysis.json"
)

WINDOW_MINUTES = 30


def parse_utc(value: str) -> datetime:
    dt = datetime.fromisoformat(
        value.replace("Z", "+00:00")
    )

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    return dt.astimezone(timezone.utc)


def nearest_record(records, target):
    return min(
        records,
        key=lambda record:
            abs(
                (
                    record["timestamp"] - target
                ).total_seconds()
            ),
    )


def main():
    grouped = defaultdict(list)

    with COMPARISON_PATH.open(
        "r",
        encoding="utf-8",
    ) as f:
        reader = csv.DictReader(f)

        for row in reader:
            grouped[row["product"]].append(
                {
                    "timestamp":
                        parse_utc(
                            row[
                                "comparison_timestamp_utc"
                            ]
                        ),

                    "position_difference_km":
                        float(
                            row[
                                "position_difference_km"
                            ]
                        ),

                    "velocity_difference_m_s":
                        float(
                            row[
                                "velocity_difference_m_s"
                            ]
                        ),
                }
            )

    for records in grouped.values():
        records.sort(
            key=lambda r: r["timestamp"]
        )

    with EVENTS_PATH.open(
        "r",
        encoding="utf-8",
    ) as f:
        events = json.load(f)

    results = []

    print()
    print("Trajectory Event Window Analysis")
    print("--------------------------------")

    for event in events:
        event_time = parse_utc(
            event["timestamp_utc"]
        )

        before_time = (
            event_time
            - timedelta(
                minutes=WINDOW_MINUTES
            )
        )

        after_time = (
            event_time
            + timedelta(
                minutes=WINDOW_MINUTES
            )
        )

        event_result = {
            "event_id": event["id"],
            "event_name": event["name"],
            "event_time_utc":
                event_time.isoformat(),
            "window_minutes":
                WINDOW_MINUTES,
            "products": [],
        }

        print()
        print(
            f"{event['short_name']} "
            f"{event_time.isoformat()}"
        )

        for product, records in sorted(
            grouped.items()
        ):
            if (
                event_time < records[0]["timestamp"]
                or event_time > records[-1]["timestamp"]
            ):
                continue

            before = nearest_record(
                records,
                before_time,
            )

            at_event = nearest_record(
                records,
                event_time,
            )

            after = nearest_record(
                records,
                after_time,
            )

            before_difference = (
                before[
                    "position_difference_km"
                ]
            )

            event_difference = (
                at_event[
                    "position_difference_km"
                ]
            )

            after_difference = (
                after[
                    "position_difference_km"
                ]
            )

            change = (
                after_difference
                - before_difference
            )

            product_result = {
                "product": product,

                "before": {
                    "timestamp_utc":
                        before[
                            "timestamp"
                        ].isoformat(),

                    "position_difference_km":
                        before_difference,
                },

                "at_event": {
                    "timestamp_utc":
                        at_event[
                            "timestamp"
                        ].isoformat(),

                    "position_difference_km":
                        event_difference,
                },

                "after": {
                    "timestamp_utc":
                        after[
                            "timestamp"
                        ].isoformat(),

                    "position_difference_km":
                        after_difference,
                },

                "window_change_km":
                    change,
            }

            event_result[
                "products"
            ].append(
                product_result
            )

            print(
                f"  {product[:34]:34} "
                f"{before_difference:8.2f} -> "
                f"{event_difference:8.2f} -> "
                f"{after_difference:8.2f} km "
                f"(Δ {change:+.2f})"
            )

        results.append(event_result)

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT_PATH.open(
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            {
                "window_minutes":
                    WINDOW_MINUTES,

                "interpretation_warning":
                    (
                        "Changes inside an event window "
                        "show temporal behavior only. "
                        "They do not establish causation "
                        "between the event and OEM solution "
                        "differences."
                    ),

                "events":
                    results,
            },
            f,
            indent=2,
        )

    print()
    print(f"Wrote: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()