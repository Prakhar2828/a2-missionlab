from __future__ import annotations

import csv
import json
import math
from datetime import datetime, timedelta
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[2]

MACH_CSV = (
    ROOT
    / "data"
    / "processed"
    / "entry"
    / "entry_mach.csv"
)

MODEL_JSON = (
    ROOT
    / "data"
    / "reference"
    / "artemis_ii_rarefaction_model.json"
)

OUTPUT_CSV = (
    ROOT
    / "data"
    / "processed"
    / "entry"
    / "entry_rarefaction.csv"
)

OUTPUT_SUMMARY = (
    ROOT
    / "data"
    / "processed"
    / "entry"
    / "entry_rarefaction_summary.json"
)

ASSET_DIR = (
    ROOT
    / "docs"
    / "assets"
    / "entry"
)


plt.rcParams["svg.hashsalt"] = (
    "a2-missionlab"
)

SVG_METADATA = {
    "Date": None,
}


def normalize_svg(
    path: Path,
):
    text = path.read_text(
        encoding="utf-8"
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
    return datetime.fromisoformat(
        value.replace(
            "Z",
            "+00:00",
        )
    )


def format_utc(
    value: datetime,
) -> str:
    return (
        value.isoformat(
            timespec="microseconds"
        )
        .replace(
            "+00:00",
            "Z",
        )
    )


def mean_free_path(
    number_density,
    collision_diameter,
):
    return (
        1.0
        / (
            math.sqrt(2.0)
            * math.pi
            * collision_diameter**2
            * number_density
        )
    )


def classify(
    kn,
):
    if kn < 0.01:
        return "CONTINUUM"

    if kn < 0.1:
        return "SLIP"

    if kn < 10.0:
        return "TRANSITION"

    return "FREE_MOLECULAR"


def descending_crossings(
    time_s,
    values,
    target,
):
    results = []

    for i in range(
        1,
        len(values),
    ):
        if not (
            values[i - 1] > target
            and values[i] <= target
        ):
            continue

        fraction = (
            target
            - values[i - 1]
        ) / (
            values[i]
            - values[i - 1]
        )

        results.append(
            float(
                time_s[i - 1]
                + fraction
                * (
                    time_s[i]
                    - time_s[i - 1]
                )
            )
        )

    return results


def interp(
    time_s,
    values,
    target,
):
    return float(
        np.interp(
            target,
            time_s,
            values,
        )
    )


def state_at(
    start,
    t,
    time_s,
    altitude,
    mach,
    mean_free_path_values,
):
    return {
        "utc":
            format_utc(
                start
                + timedelta(
                    seconds=t
                )
            ),

        "ei_elapsed_seconds":
            float(t),

        "altitude_km":
            interp(
                time_s,
                altitude,
                t,
            ),

        "mach":
            interp(
                time_s,
                mach,
                t,
            ),

        "mean_free_path_m":
            interp(
                time_s,
                mean_free_path_values,
                t,
            ),
    }


def main():
    for path in [
        MACH_CSV,
        MODEL_JSON,
    ]:
        if not path.exists():
            raise SystemExit(
                f"Missing required file:\n"
                f"{path}"
            )

    with MACH_CSV.open(
        "r",
        encoding="utf-8",
    ) as f:
        reader = csv.DictReader(f)

        input_fields = (
            reader.fieldnames
            or []
        )

        rows = list(reader)

    with MODEL_JSON.open(
        "r",
        encoding="utf-8-sig",
    ) as f:
        model = json.load(f)

    if len(rows) != 819:
        raise SystemExit(
            f"Expected 819 states, "
            f"found {len(rows)}"
        )

    characteristic_length = float(
        model[
            "characteristic_length"
        ][
            "value_m"
        ]
    )

    reference_diameter = float(
        model[
            "collision_model"
        ][
            "reference_collision_diameter_m"
        ]
    )

    sensitivity_diameters = [
        float(value)
        for value in model[
            "collision_model"
        ][
            "sensitivity_collision_diameters_m"
        ]
    ]

    timestamps = [
        parse_utc(
            row[
                "timestamp_utc"
            ]
        )
        for row in rows
    ]

    start = timestamps[0]

    time_s = np.array(
        [
            (
                timestamp
                - start
            ).total_seconds()
            for timestamp
            in timestamps
        ],
        dtype=float,
    )

    altitude = np.array(
        [
            float(
                row[
                    "wgs84_altitude_km"
                ]
            )
            for row in rows
        ],
        dtype=float,
    )

    mach = np.array(
        [
            float(
                row[
                    "modeled_free_stream_mach"
                ]
            )
            for row in rows
        ],
        dtype=float,
    )

    number_density = np.array(
        [
            float(
                row[
                    "thermal_particle_number_density_m3"
                ]
            )
            for row in rows
        ],
        dtype=float,
    )

    dynamic_pressure = np.array(
        [
            float(
                row[
                    "modeled_dynamic_pressure_pa"
                ]
            )
            for row in rows
        ],
        dtype=float,
    )

    if not np.all(
        number_density > 0.0
    ):
        raise SystemExit(
            "Non-positive thermal "
            "number density found."
        )

    lambda_ref = np.array(
        [
            mean_free_path(
                n,
                reference_diameter,
            )
            for n
            in number_density
        ],
        dtype=float,
    )

    kn_ref = (
        lambda_ref
        / characteristic_length
    )

    sensitivity = {}

    for diameter in (
        sensitivity_diameters
    ):
        lambda_values = np.array(
            [
                mean_free_path(
                    n,
                    diameter,
                )
                for n
                in number_density
            ],
            dtype=float,
        )

        kn_values = (
            lambda_values
            / characteristic_length
        )

        crossings = (
            descending_crossings(
                time_s,
                kn_values,
                0.01,
            )
        )

        if not crossings:
            raise SystemExit(
                "Missing Kn=0.01 "
                "sensitivity crossing."
            )

        t = crossings[-1]

        sensitivity[
            f"{diameter:.12e}"
        ] = {
            "collision_diameter_m":
                diameter,

            "kn_0_01_ei_elapsed_seconds":
                t,

            "kn_0_01_altitude_km":
                interp(
                    time_s,
                    altitude,
                    t,
                ),
        }

    threshold_results = {}

    for threshold in [
        10.0,
        0.1,
        0.01,
        0.001,
    ]:
        matches = (
            descending_crossings(
                time_s,
                kn_ref,
                threshold,
            )
        )

        key = f"{threshold:g}"

        if not matches:
            threshold_results[key] = None
            continue

        t = matches[-1]

        result = state_at(
            start,
            t,
            time_s,
            altitude,
            mach,
            lambda_ref,
        )

        result[
            "knudsen_number"
        ] = threshold

        threshold_results[
            key
        ] = result

    max_mach_index = int(
        np.argmax(
            mach
        )
    )

    local_q_maxima = []

    for i in range(
        1,
        len(
            dynamic_pressure
        ) - 1,
    ):
        if (
            dynamic_pressure[i]
            > dynamic_pressure[i - 1]
            and dynamic_pressure[i]
            >= dynamic_pressure[i + 1]
        ):
            local_q_maxima.append(i)

    local_q_maxima = sorted(
        local_q_maxima,
        key=lambda index:
            dynamic_pressure[index],
        reverse=True,
    )

    q_peak_context = []

    for index in (
        local_q_maxima[:2]
    ):
        q_peak_context.append(
            {
                "utc":
                    rows[index][
                        "timestamp_utc"
                    ],

                "ei_elapsed_seconds":
                    float(
                        time_s[index]
                    ),

                "altitude_km":
                    float(
                        altitude[index]
                    ),

                "mach":
                    float(
                        mach[index]
                    ),

                "dynamic_pressure_pa":
                    float(
                        dynamic_pressure[index]
                    ),

                "mean_free_path_m":
                    float(
                        lambda_ref[index]
                    ),

                "body_scale_knudsen":
                    float(
                        kn_ref[index]
                    ),

                "body_scale_regime":
                    classify(
                        kn_ref[index]
                    ),
            }
        )

    appended_fields = [
        "reference_hard_sphere_mean_free_path_m",
        "body_scale_characteristic_length_m",
        "body_scale_knudsen_number",
        "body_scale_rarefaction_regime",
    ]

    OUTPUT_CSV.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT_CSV.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=(
                input_fields
                + appended_fields
            ),
        )

        writer.writeheader()

        for i, row in enumerate(
            rows
        ):
            output_row = dict(row)

            output_row.update(
                {
                    "reference_hard_sphere_mean_free_path_m":
                        lambda_ref[i],

                    "body_scale_characteristic_length_m":
                        characteristic_length,

                    "body_scale_knudsen_number":
                        kn_ref[i],

                    "body_scale_rarefaction_regime":
                        classify(
                            kn_ref[i]
                        ),
                }
            )

            writer.writerow(
                output_row
            )

    summary = {
        "provenance": {
            "thermal_number_density":
                "MODEL_DERIVED",

            "mean_free_path":
                "MODEL",

            "body_scale_knudsen":
                "MODEL_DERIVED",

            "rarefaction_regime":
                "MODEL_DERIVED",
        },

        "model": model,

        "records":
            len(rows),

        "entry_interface": {
            "utc":
                rows[0][
                    "timestamp_utc"
                ],

            "altitude_km":
                float(
                    altitude[0]
                ),

            "mach":
                float(
                    mach[0]
                ),

            "thermal_number_density_m3":
                float(
                    number_density[0]
                ),

            "mean_free_path_m":
                float(
                    lambda_ref[0]
                ),

            "body_scale_knudsen":
                float(
                    kn_ref[0]
                ),

            "body_scale_regime":
                classify(
                    kn_ref[0]
                ),
        },

        "maximum_formal_mach_state": {
            "utc":
                rows[
                    max_mach_index
                ][
                    "timestamp_utc"
                ],

            "ei_elapsed_seconds":
                float(
                    time_s[
                        max_mach_index
                    ]
                ),

            "altitude_km":
                float(
                    altitude[
                        max_mach_index
                    ]
                ),

            "mach":
                float(
                    mach[
                        max_mach_index
                    ]
                ),

            "thermal_number_density_m3":
                float(
                    number_density[
                        max_mach_index
                    ]
                ),

            "mean_free_path_m":
                float(
                    lambda_ref[
                        max_mach_index
                    ]
                ),

            "body_scale_knudsen":
                float(
                    kn_ref[
                        max_mach_index
                    ]
                ),

            "body_scale_regime":
                classify(
                    kn_ref[
                        max_mach_index
                    ]
                ),
        },

        "knudsen_threshold_crossings":
            threshold_results,

        "collision_diameter_sensitivity":
            sensitivity,

        "dynamic_pressure_peak_context":
            q_peak_context,

        "interpretation_limits":
            model[
                "interpretation_limits"
            ],
    }

    with OUTPUT_SUMMARY.open(
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            summary,
            f,
            indent=2,
        )

    ASSET_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    history_path = (
        ASSET_DIR
        / "phase2e_knudsen_history.svg"
    )

    fig, ax = plt.subplots()

    ax.semilogy(
        time_s,
        kn_ref,
    )

    for threshold in [
        0.1,
        0.01,
        0.001,
    ]:
        ax.axhline(
            threshold,
            linewidth=0.8,
        )

    ax.set_xlabel(
        "Seconds after Entry Interface"
    )

    ax.set_ylabel(
        "Body-scale Knudsen number"
    )

    ax.set_title(
        "Artemis II Body-Scale Rarefaction History"
    )

    ax.grid(
        True,
        alpha=0.25,
    )

    fig.tight_layout()

    fig.savefig(
        history_path,
        format="svg",
        metadata=SVG_METADATA,
    )

    plt.close(fig)

    normalize_svg(
        history_path
    )

    altitude_path = (
        ASSET_DIR
        / "phase2e_knudsen_altitude.svg"
    )

    fig, ax = plt.subplots()

    ax.semilogx(
        kn_ref,
        altitude,
    )

    for threshold in [
        0.1,
        0.01,
        0.001,
    ]:
        ax.axvline(
            threshold,
            linewidth=0.8,
        )

    ax.set_xlabel(
        "Body-scale Knudsen number"
    )

    ax.set_ylabel(
        "WGS84 altitude (km)"
    )

    ax.set_title(
        "Artemis II Body-Scale Knudsen Number vs Altitude"
    )

    ax.grid(
        True,
        alpha=0.25,
    )

    fig.tight_layout()

    fig.savefig(
        altitude_path,
        format="svg",
        metadata=SVG_METADATA,
    )

    plt.close(fig)

    normalize_svg(
        altitude_path
    )

    print()
    print(
        "Artemis II Body-Scale "
        "Rarefaction"
    )

    print(
        "------------------------------"
    )

    print(
        f"Records: "
        f"{len(rows)}"
    )

    print(
        f"Characteristic length: "
        f"{characteristic_length:.3f} m"
    )

    print(
        "Reference collision diameter: "
        f"{reference_diameter:.3e} m"
    )

    print()
    print(
        "Entry Interface:"
    )

    print(
        f"  mean free path: "
        f"{lambda_ref[0]:.9f} m"
    )

    print(
        f"  Kn: "
        f"{kn_ref[0]:.9f}"
    )

    print(
        f"  regime: "
        f"{classify(kn_ref[0])}"
    )

    print()
    print(
        "Maximum formal Mach state:"
    )

    print(
        f"  altitude: "
        f"{altitude[max_mach_index]:.6f} km"
    )

    print(
        f"  Mach: "
        f"{mach[max_mach_index]:.6f}"
    )

    print(
        f"  mean free path: "
        f"{lambda_ref[max_mach_index]:.9f} m"
    )

    print(
        f"  Kn: "
        f"{kn_ref[max_mach_index]:.9f}"
    )

    print(
        f"  regime: "
        f"{classify(kn_ref[max_mach_index])}"
    )

    print()
    print(
        "Descending Kn thresholds:"
    )

    for key in [
        "0.1",
        "0.01",
        "0.001",
    ]:
        state = (
            threshold_results[
                key
            ]
        )

        print(
            f"  Kn={key}: "
            f"EI+"
            f"{state['ei_elapsed_seconds']:.6f}s, "
            f"h="
            f"{state['altitude_km']:.6f} km, "
            f"M="
            f"{state['mach']:.6f}"
        )

    print()
    print(
        "Collision-diameter sensitivity for Kn=0.01:"
    )

    for result in (
        sensitivity.values()
    ):
        print(
            f"  d="
            f"{result['collision_diameter_m']:.3e} m: "
            f"h="
            f"{result['kn_0_01_altitude_km']:.6f} km"
        )

    print()
    print(
        "Dynamic-pressure peaks:"
    )

    for peak in (
        q_peak_context
    ):
        print(
            f"  {peak['utc']}  "
            f"h={peak['altitude_km']:.6f} km  "
            f"M={peak['mach']:.6f}  "
            f"Kn={peak['body_scale_knudsen']:.12e}  "
            f"{peak['body_scale_regime']}"
        )

    print()
    print(
        "IMPORTANT:"
    )

    print(
        "This is a body-scale "
        "rarefaction indicator."
    )

    print(
        "It is not a local-gradient "
        "or shock-layer breakdown criterion."
    )

    print()
    print(
        f"Wrote: "
        f"{OUTPUT_CSV.relative_to(ROOT)}"
    )

    print(
        f"Wrote: "
        f"{OUTPUT_SUMMARY.relative_to(ROOT)}"
    )

    print(
        "Wrote documentation SVGs "
        f"under {ASSET_DIR.relative_to(ROOT)}"
    )


if __name__ == "__main__":
    main()
