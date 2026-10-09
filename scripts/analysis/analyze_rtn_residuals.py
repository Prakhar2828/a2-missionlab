from __future__ import annotations

import csv
import json
import math
import re
from bisect import bisect_right
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np


TRAJECTORY_DIR = Path("data/processed/trajectory")
MANIFEST_PATH = TRAJECTORY_DIR / "manifest.json"
CONFIG_PATH = Path("data/config/mission.json")
EVENTS_PATH = Path("data/reference/trajectory_events.json")

OUTPUT_DETAIL = (
    TRAJECTORY_DIR / "oem_rtn_residuals.csv"
)

OUTPUT_SUMMARY = (
    TRAJECTORY_DIR / "oem_rtn_summary.json"
)

PLOT_DIR = Path(
    "docs/assets/rtn"
)


def parse_utc(value: str) -> datetime:
    dt = datetime.fromisoformat(
        value.replace("Z", "+00:00")
    )

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    return dt.astimezone(timezone.utc)


def state_from_row(row):
    position = np.array(
        [
            float(row["x_km"]),
            float(row["y_km"]),
            float(row["z_km"]),
        ],
        dtype=float,
    )

    velocity = np.array(
        [
            float(row["vx_km_s"]),
            float(row["vy_km_s"]),
            float(row["vz_km_s"]),
        ],
        dtype=float,
    )

    return position, velocity


def load_product(path: Path):
    with path.open(
        "r",
        encoding="utf-8",
    ) as f:
        rows = list(csv.DictReader(f))

    times = [
        parse_utc(row["timestamp_utc"])
        for row in rows
    ]

    return rows, times


def interpolate_state(
    rows,
    times,
    target_time,
):
    if (
        target_time < times[0]
        or target_time > times[-1]
    ):
        return None

    index = bisect_right(
        times,
        target_time,
    )

    if index == 0:
        return state_from_row(rows[0])

    if index >= len(rows):
        return state_from_row(rows[-1])

    row0 = rows[index - 1]
    row1 = rows[index]

    t0 = times[index - 1]
    t1 = times[index]

    if target_time == t0:
        return state_from_row(row0)

    if target_time == t1:
        return state_from_row(row1)

    dt = (t1 - t0).total_seconds()

    u = (
        target_time - t0
    ).total_seconds() / dt

    p0, v0 = state_from_row(row0)
    p1, v1 = state_from_row(row1)

    h00 = 2 * u**3 - 3 * u**2 + 1
    h10 = u**3 - 2 * u**2 + u
    h01 = -2 * u**3 + 3 * u**2
    h11 = u**3 - u**2

    position = (
        h00 * p0
        + h10 * dt * v0
        + h01 * p1
        + h11 * dt * v1
    )

    dh00 = 6 * u**2 - 6 * u
    dh10 = 3 * u**2 - 4 * u + 1
    dh01 = -6 * u**2 + 6 * u
    dh11 = 3 * u**2 - 2 * u

    velocity = (
        dh00 * p0
        + dh10 * dt * v0
        + dh01 * p1
        + dh11 * dt * v1
    ) / dt

    return position, velocity


def rtn_basis(
    position,
    velocity,
):
    r_norm = np.linalg.norm(position)

    if r_norm == 0:
        raise ValueError(
            "Cannot construct RTN basis "
            "from zero position vector."
        )

    r_hat = position / r_norm

    angular_momentum = np.cross(
        position,
        velocity,
    )

    h_norm = np.linalg.norm(
        angular_momentum
    )

    if h_norm == 0:
        raise ValueError(
            "Cannot construct RTN basis "
            "from zero angular momentum."
        )

    n_hat = (
        angular_momentum / h_norm
    )

    t_hat = np.cross(
        n_hat,
        r_hat,
    )

    t_hat = (
        t_hat
        / np.linalg.norm(t_hat)
    )

    return r_hat, t_hat, n_hat


def project_rtn(
    vector,
    basis,
):
    r_hat, t_hat, n_hat = basis

    return np.array(
        [
            np.dot(vector, r_hat),
            np.dot(vector, t_hat),
            np.dot(vector, n_hat),
        ]
    )


def rms(values):
    values = np.asarray(
        values,
        dtype=float,
    )

    return float(
        np.sqrt(
            np.mean(values**2)
        )
    )


def median_abs(values):
    values = np.asarray(
        values,
        dtype=float,
    )

    return float(
        np.median(
            np.abs(values)
        )
    )


def max_abs(values):
    values = np.asarray(
        values,
        dtype=float,
    )

    return float(
        np.max(
            np.abs(values)
        )
    )


def dominant_component(
    r_value,
    t_value,
    n_value,
):
    values = {
        "R": abs(r_value),
        "T": abs(t_value),
        "N": abs(n_value),
    }

    return max(
        values,
        key=values.get,
    )


def summarize_components(
    records,
    prefix,
):
    keys = {
        "R": f"{prefix}_r",
        "T": f"{prefix}_t",
        "N": f"{prefix}_n",
    }

    summary = {}

    for axis, key in keys.items():
        values = [
            record[key]
            for record in records
        ]

        summary[axis] = {
            "rms":
                rms(values),

            "median_absolute":
                median_abs(values),

            "maximum_absolute":
                max_abs(values),
        }

    dominant_counts = Counter(
        record[
            f"{prefix}_dominant"
        ]
        for record in records
    )

    total = len(records)

    summary[
        "dominant_epoch_fraction"
    ] = {
        axis: (
            dominant_counts[axis]
            / total
        )
        for axis in ["R", "T", "N"]
    }

    dominant_rms_axis = max(
        ["R", "T", "N"],
        key=lambda axis:
            summary[axis]["rms"],
    )

    summary[
        "dominant_rms_axis"
    ] = dominant_rms_axis

    return summary


def sanitize_filename(value: str) -> str:
    value = re.sub(
        r"[^A-Za-z0-9]+",
        "_",
        value,
    )

    return value.strip("_")


def load_events():
    if not EVENTS_PATH.exists():
        return []

    with EVENTS_PATH.open(
        "r",
        encoding="utf-8",
    ) as f:
        events = json.load(f)

    for event in events:
        event["parsed_time"] = (
            parse_utc(
                event["timestamp_utc"]
            )
        )

    return events


def add_event_lines(
    ax,
    events,
):
    for event in events:
        ax.axvline(
            event["parsed_time"],
            linestyle="--",
            linewidth=0.8,
            alpha=0.6,
        )

        ax.text(
            event["parsed_time"],
            0.97,
            event["short_name"],
            rotation=90,
            fontsize=7,
            verticalalignment="top",
            horizontalalignment="right",
            transform=ax.get_xaxis_transform(),
        )


def plot_product(
    product,
    records,
    events,
):
    PLOT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    records = sorted(
        records,
        key=lambda record:
            record["timestamp"],
    )

    timestamps = [
        record["timestamp"]
        for record in records
    ]

    safe_name = sanitize_filename(
        product.replace(".csv", "")
    )

    # Position residual plot
    fig, ax = plt.subplots(
        figsize=(14, 7)
    )

    ax.plot(
        timestamps,
        [
            record["dr_r"]
            for record in records
        ],
        label="ΔR radial",
    )

    ax.plot(
        timestamps,
        [
            record["dr_t"]
            for record in records
        ],
        label="ΔT along-track",
    )

    ax.plot(
        timestamps,
        [
            record["dr_n"]
            for record in records
        ],
        label="ΔN cross-track",
    )

    ax.axhline(
        0,
        linewidth=0.8,
    )

    add_event_lines(
        ax,
        events,
    )

    ax.set_title(
        f"RTN Position Residuals\n{product}"
    )

    ax.set_xlabel("UTC")
    ax.set_ylabel(
        "Comparison OEM − April 10 OEM (km)"
    )

    ax.grid(
        True,
        alpha=0.25,
    )

    ax.legend()

    ax.xaxis.set_major_formatter(
        mdates.DateFormatter(
            "%b %d",
            tz=timezone.utc,
        )
    )

    fig.autofmt_xdate()
    fig.tight_layout()

    position_path = (
        PLOT_DIR
        / f"{safe_name}_position.svg"
    )

    fig.savefig(
        position_path,
        format="svg",
        bbox_inches="tight",
    )

    plt.close(fig)

    # Velocity residual plot
    fig, ax = plt.subplots(
        figsize=(14, 7)
    )

    ax.plot(
        timestamps,
        [
            record["dv_r"]
            for record in records
        ],
        label="Δv_R radial",
    )

    ax.plot(
        timestamps,
        [
            record["dv_t"]
            for record in records
        ],
        label="Δv_T along-track",
    )

    ax.plot(
        timestamps,
        [
            record["dv_n"]
            for record in records
        ],
        label="Δv_N cross-track",
    )

    ax.axhline(
        0,
        linewidth=0.8,
    )

    add_event_lines(
        ax,
        events,
    )

    ax.set_title(
        f"RTN Velocity Residuals\n{product}"
    )

    ax.set_xlabel("UTC")
    ax.set_ylabel(
        "Comparison OEM − April 10 OEM (m/s)"
    )

    ax.grid(
        True,
        alpha=0.25,
    )

    ax.legend()

    ax.xaxis.set_major_formatter(
        mdates.DateFormatter(
            "%b %d",
            tz=timezone.utc,
        )
    )

    fig.autofmt_xdate()
    fig.tight_layout()

    velocity_path = (
        PLOT_DIR
        / f"{safe_name}_velocity.svg"
    )

    fig.savefig(
        velocity_path,
        format="svg",
        bbox_inches="tight",
    )

    plt.close(fig)

    return (
        str(position_path),
        str(velocity_path),
    )


def main():
    with CONFIG_PATH.open(
        "r",
        encoding="utf-8",
    ) as f:
        config = json.load(f)

    with MANIFEST_PATH.open(
        "r",
        encoding="utf-8",
    ) as f:
        manifest = json.load(f)

    reference_name = (
        config["primary_oem"]
    )

    reference_path = (
        TRAJECTORY_DIR
        / reference_name
    )

    reference_rows, reference_times = (
        load_product(
            reference_path
        )
    )

    events = load_events()

    detail_records = []
    summary = {}

    print()
    print(
        "Artemis II OEM RTN Residual Analysis"
    )
    print(
        "------------------------------------"
    )

    print(
        f"Reference: {reference_name}"
    )
    print()

    for product in manifest:
        product_path = Path(
            product["output_csv"]
        )

        if (
            product_path.name
            == reference_name
        ):
            continue

        rows, times = load_product(
            product_path
        )

        metadata_path = Path(
            product["metadata_file"]
        )

        with metadata_path.open(
            "r",
            encoding="utf-8",
        ) as f:
            metadata = json.load(f)

        creation_time = parse_utc(
            metadata["CREATION_DATE"]
        )

        product_records = []

        for (
            reference_row,
            target_time,
        ) in zip(
            reference_rows,
            reference_times,
        ):
            comparison_state = (
                interpolate_state(
                    rows,
                    times,
                    target_time,
                )
            )

            if comparison_state is None:
                continue

            (
                reference_position,
                reference_velocity,
            ) = state_from_row(
                reference_row
            )

            (
                comparison_position,
                comparison_velocity,
            ) = comparison_state

            basis = rtn_basis(
                reference_position,
                reference_velocity,
            )

            delta_position = (
                comparison_position
                - reference_position
            )

            delta_velocity = (
                comparison_velocity
                - reference_velocity
            )

            position_rtn = project_rtn(
                delta_position,
                basis,
            )

            velocity_rtn_km_s = (
                project_rtn(
                    delta_velocity,
                    basis,
                )
            )

            velocity_rtn_m_s = (
                velocity_rtn_km_s
                * 1000.0
            )

            record = {
                "product":
                    product_path.name,

                "timestamp":
                    target_time,

                "epoch_class":
                    (
                        "AT_OR_BEFORE_PRODUCT_CREATION"
                        if target_time
                        <= creation_time
                        else "AFTER_PRODUCT_CREATION"
                    ),

                "dr_r":
                    float(
                        position_rtn[0]
                    ),

                "dr_t":
                    float(
                        position_rtn[1]
                    ),

                "dr_n":
                    float(
                        position_rtn[2]
                    ),

                "dr_norm":
                    float(
                        np.linalg.norm(
                            delta_position
                        )
                    ),

                "dr_dominant":
                    dominant_component(
                        *position_rtn
                    ),

                "dv_r":
                    float(
                        velocity_rtn_m_s[0]
                    ),

                "dv_t":
                    float(
                        velocity_rtn_m_s[1]
                    ),

                "dv_n":
                    float(
                        velocity_rtn_m_s[2]
                    ),

                "dv_norm":
                    float(
                        np.linalg.norm(
                            velocity_rtn_m_s
                        )
                    ),

                "dv_dominant":
                    dominant_component(
                        *velocity_rtn_m_s
                    ),
            }

            product_records.append(
                record
            )

            detail_records.append(
                record
            )

        position_summary = (
            summarize_components(
                product_records,
                "dr",
            )
        )

        velocity_summary = (
            summarize_components(
                product_records,
                "dv",
            )
        )

        (
            position_plot,
            velocity_plot,
        ) = plot_product(
            product_path.name,
            product_records,
            events,
        )

        summary[
            product_path.name
        ] = {
            "creation_date":
                metadata[
                    "CREATION_DATE"
                ],

            "common_epochs":
                len(product_records),

            "position_rtn_km":
                position_summary,

            "velocity_rtn_m_s":
                velocity_summary,

            "plots": {
                "position":
                    position_plot,

                "velocity":
                    velocity_plot,
            },
        }

        print(
            product_path.name
        )

        print(
            "  Position RMS:"
        )

        print(
            "    R radial:      "
            f"{position_summary['R']['rms']:9.3f} km"
        )

        print(
            "    T along-track: "
            f"{position_summary['T']['rms']:9.3f} km"
        )

        print(
            "    N cross-track: "
            f"{position_summary['N']['rms']:9.3f} km"
        )

        print(
            "  Dominant position axis: "
            f"{position_summary['dominant_rms_axis']}"
        )

        print(
            "  Position dominant fractions:"
        )

        print(
            "    R: "
            f"{position_summary['dominant_epoch_fraction']['R']:.1%}"
        )

        print(
            "    T: "
            f"{position_summary['dominant_epoch_fraction']['T']:.1%}"
        )

        print(
            "    N: "
            f"{position_summary['dominant_epoch_fraction']['N']:.1%}"
        )

        print(
            "  Velocity RMS:"
        )

        print(
            "    R radial:      "
            f"{velocity_summary['R']['rms']:9.3f} m/s"
        )

        print(
            "    T along-track: "
            f"{velocity_summary['T']['rms']:9.3f} m/s"
        )

        print(
            "    N cross-track: "
            f"{velocity_summary['N']['rms']:9.3f} m/s"
        )

        print(
            "  Dominant velocity axis: "
            f"{velocity_summary['dominant_rms_axis']}"
        )

        print()

    OUTPUT_DETAIL.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT_DETAIL.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as f:
        fieldnames = [
            "product",
            "timestamp_utc",
            "epoch_class",

            "delta_r_radial_km",
            "delta_r_along_track_km",
            "delta_r_cross_track_km",
            "delta_r_norm_km",
            "dominant_position_axis",

            "delta_v_radial_m_s",
            "delta_v_along_track_m_s",
            "delta_v_cross_track_m_s",
            "delta_v_norm_m_s",
            "dominant_velocity_axis",
        ]

        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames,
        )

        writer.writeheader()

        for record in detail_records:
            writer.writerow(
                {
                    "product":
                        record[
                            "product"
                        ],

                    "timestamp_utc":
                        record[
                            "timestamp"
                        ].isoformat(),

                    "epoch_class":
                        record[
                            "epoch_class"
                        ],

                    "delta_r_radial_km":
                        record[
                            "dr_r"
                        ],

                    "delta_r_along_track_km":
                        record[
                            "dr_t"
                        ],

                    "delta_r_cross_track_km":
                        record[
                            "dr_n"
                        ],

                    "delta_r_norm_km":
                        record[
                            "dr_norm"
                        ],

                    "dominant_position_axis":
                        record[
                            "dr_dominant"
                        ],

                    "delta_v_radial_m_s":
                        record[
                            "dv_r"
                        ],

                    "delta_v_along_track_m_s":
                        record[
                            "dv_t"
                        ],

                    "delta_v_cross_track_m_s":
                        record[
                            "dv_n"
                        ],

                    "delta_v_norm_m_s":
                        record[
                            "dv_norm"
                        ],

                    "dominant_velocity_axis":
                        record[
                            "dv_dominant"
                        ],
                }
            )

    with OUTPUT_SUMMARY.open(
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            {
                "reference_product":
                    reference_name,

                "frame_definition": {
                    "center":
                        "EARTH",

                    "reference_state":
                        "April 10 public OEM",

                    "R":
                        (
                            "Earth-centered radial "
                            "direction."
                        ),

                    "T":
                        (
                            "Transverse/along-track "
                            "direction defined by "
                            "N cross R."
                        ),

                    "N":
                        (
                            "Direction of reference "
                            "specific angular momentum "
                            "r cross v."
                        ),
                },

                "interpretation_warning":
                    (
                        "RTN components describe "
                        "solution-to-solution state "
                        "differences in the Earth-centered "
                        "RTN frame of the April 10 "
                        "reference trajectory. They are "
                        "not navigation errors or flight "
                        "control tolerances. Velocity "
                        "components are projections of "
                        "inertial delta-vectors and are "
                        "not time derivatives of rotating "
                        "RTN position coordinates."
                    ),

                "products":
                    summary,
            },
            f,
            indent=2,
        )

    print(
        f"Wrote: {OUTPUT_DETAIL}"
    )

    print(
        f"Wrote: {OUTPUT_SUMMARY}"
    )

    print(
        f"Wrote RTN plots under: "
        f"{PLOT_DIR}"
    )


if __name__ == "__main__":
    main()