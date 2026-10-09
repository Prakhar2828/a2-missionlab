from __future__ import annotations

import csv
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.dates as mdates


plt.rcParams["svg.hashsalt"] = "a2-missionlab"
SVG_METADATA = {"Date": None}


COMPARISON_PATH = Path(
    "data/processed/trajectory/oem_comparison_detail.csv"
)

EVENTS_PATH = Path(
    "data/reference/trajectory_events.json"
)

OUTPUT_PATH = Path(
    "docs/assets/phase1f_oem_with_events.svg"
)


def normalize_svg(
    path: Path,
):
    text = path.read_text(
        encoding="utf-8",
    )

    cleaned = "\n".join(
        line.rstrip(" \t")
        for line in text.splitlines()
    ) + "\n"

    path.write_text(
        cleaned,
        encoding="utf-8",
    )


def parse_utc(
    value: str,
) -> datetime:
    dt = datetime.fromisoformat(
        value.replace(
            "Z",
            "+00:00",
        )
    )

    if dt.tzinfo is None:
        dt = dt.replace(
            tzinfo=timezone.utc
        )

    return dt.astimezone(
        timezone.utc
    )


def short_product_name(
    product: str,
) -> str:
    return (
        product
        .replace(
            "Artemis_II_OEM_",
            "",
        )
        .replace(
            ".csv",
            "",
        )
        .replace(
            "_",
            " ",
        )
    )


def main():
    grouped = defaultdict(
        list
    )

    with COMPARISON_PATH.open(
        "r",
        encoding="utf-8",
    ) as f:
        reader = csv.DictReader(
            f
        )

        for row in reader:
            grouped[
                row["product"]
            ].append(
                {
                    "timestamp":
                        parse_utc(
                            row[
                                "comparison_timestamp_utc"
                            ]
                        ),

                    "difference_km":
                        float(
                            row[
                                "position_difference_km"
                            ]
                        ),
                }
            )

    with EVENTS_PATH.open(
        "r",
        encoding="utf-8",
    ) as f:
        events = json.load(
            f
        )

    fig, ax = plt.subplots(
        figsize=(15, 8)
    )

    for product, records in sorted(
        grouped.items()
    ):
        records.sort(
            key=lambda record:
                record[
                    "timestamp"
                ]
        )

        ax.plot(
            [
                record[
                    "timestamp"
                ]
                for record in records
            ],
            [
                record[
                    "difference_km"
                ]
                for record in records
            ],
            linewidth=1.15,
            label=short_product_name(
                product
            ),
        )

    for event in events:
        timestamp = parse_utc(
            event[
                "timestamp_utc"
            ]
        )

        if event[
            "type"
        ] == "BURN":
            linestyle = "--"
        else:
            linestyle = ":"

        ax.axvline(
            timestamp,
            linestyle=linestyle,
            linewidth=1.2,
        )

        ax.text(
            timestamp,
            ax.get_ylim()[1]
            * 0.96,
            event[
                "short_name"
            ],
            rotation=90,
            verticalalignment="top",
            horizontalalignment="right",
            fontsize=8,
        )

    ax.set_title(
        "Artemis II Public OEM Solution Evolution\n"
        "with Documented Trajectory Events"
    )

    ax.set_xlabel(
        "UTC"
    )

    ax.set_ylabel(
        "3-D Position Difference "
        "from April 10 Public OEM (km)"
    )

    ax.grid(
        True,
        alpha=0.25,
    )

    ax.xaxis.set_major_formatter(
        mdates.DateFormatter(
            "%b %d",
            tz=timezone.utc,
        )
    )

    ax.legend(
        fontsize=7,
        loc="upper right",
    )

    fig.autofmt_xdate()
    fig.tight_layout()

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fig.savefig(
        OUTPUT_PATH,
        format="svg",
        bbox_inches="tight",
        metadata=SVG_METADATA,
    )

    normalize_svg(
        OUTPUT_PATH
    )

    plt.close(
        fig
    )

    print(
        f"Loaded "
        f"{len(events)} "
        f"mission events."
    )

    for event in events:
        print(
            f"{event['short_name']:6} "
            f"{event['timestamp_utc']} "
            f"[{event['provenance']}]"
        )

    print()

    print(
        f"Wrote: {OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()