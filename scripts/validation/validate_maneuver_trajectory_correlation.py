from __future__ import annotations

import csv
import json
import math
from bisect import bisect_right
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

REFERENCE_PATH = (
    ROOT
    / "data"
    / "reference"
    / "artemis_ii_maneuver_trajectory_correlation.json"
)

MISSION_CONFIG_PATH = (
    ROOT
    / "data"
    / "config"
    / "mission.json"
)

MANEUVER_PATH = (
    ROOT
    / "data"
    / "reference"
    / "artemis_ii_maneuver_plan_execution.json"
)

PROPULSION_PATH = (
    ROOT
    / "data"
    / "reference"
    / "artemis_ii_esm_propulsion_architecture.json"
)

MISSION_PHASE_PATH = (
    ROOT
    / "data"
    / "processed"
    / "trajectory"
    / "mission_phase_summary.json"
)

ENTRY_EVENTS_PATH = (
    ROOT
    / "data"
    / "reference"
    / "artemis_ii_entry_events.json"
)

COMMUNICATIONS_PATH = (
    ROOT
    / "data"
    / "reference"
    / "artemis_ii_communications_event_catalog.json"
)

MANIFEST_PATH = (
    ROOT
    / "data"
    / "processed"
    / "trajectory"
    / "manifest.json"
)

MISSION_CLOCK_CSV = (
    ROOT
    / "data"
    / "processed"
    / "maneuvers"
    / "maneuver_mission_clock_correlation.csv"
)

OEM_BRACKET_CSV = (
    ROOT
    / "data"
    / "processed"
    / "maneuvers"
    / "maneuver_oem_solution_brackets.csv"
)

SUMMARY_PATH = (
    ROOT
    / "data"
    / "processed"
    / "maneuvers"
    / "maneuver_trajectory_correlation_summary.json"
)

MISSION_CLOCK_FIGURE = (
    ROOT
    / "docs"
    / "assets"
    / "maneuvers"
    / "phase2i3_maneuver_mission_clock.svg"
)

OEM_BRACKET_FIGURE = (
    ROOT
    / "docs"
    / "assets"
    / "maneuvers"
    / "phase2i3_oem_solution_brackets.svg"
)

EXPECTED_DATASET_ID = (
    "phase2i3_artemis_ii_maneuver_trajectory_correlation"
)

EXPECTED_PRODUCT_ID = (
    "phase2i3_maneuver_trajectory_correlation_analysis"
)

BURN_IDS = [
    "otc3",
    "rtc1",
    "rtc2",
    "rtc3",
]


def fail(message: str) -> None:
    raise SystemExit(
        "VALIDATION FAILED: "
        f"{message}"
    )


def load_json(path: Path):
    if not path.exists():
        fail(
            f"missing file: {path}"
        )

    with path.open(
        "r",
        encoding="utf-8-sig",
    ) as f:
        return json.load(f)


def parse_utc(value: str):
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


def check_close(
    label,
    observed,
    expected,
    tolerance=1e-6,
):
    if abs(
        float(observed)
        - float(expected)
    ) > tolerance:
        fail(
            f"{label}: "
            f"{observed} != {expected}"
        )


def magnitude(vector):
    return math.sqrt(
        sum(
            value * value
            for value in vector
        )
    )


def state_from_row(row):
    return (
        [
            float(row["x_km"]),
            float(row["y_km"]),
            float(row["z_km"]),
        ],
        [
            float(row["vx_km_s"]),
            float(row["vy_km_s"]),
            float(row["vz_km_s"]),
        ],
    )


def load_product(path):
    with path.open(
        "r",
        encoding="utf-8",
    ) as f:
        rows = list(
            csv.DictReader(f)
        )

    if not rows:
        fail(
            f"empty OEM product: {path}"
        )

    times = [
        parse_utc(
            row[
                "timestamp_utc"
            ]
        )
        for row in rows
    ]

    return (
        rows,
        times,
    )


def interpolate_state(
    rows,
    times,
    target,
):
    if (
        target < times[0]
        or target > times[-1]
    ):
        return None

    index = bisect_right(
        times,
        target,
    )

    if index == 0:
        return state_from_row(
            rows[0]
        )

    if index >= len(rows):
        return state_from_row(
            rows[-1]
        )

    row0 = rows[
        index - 1
    ]

    row1 = rows[
        index
    ]

    t0 = times[
        index - 1
    ]

    t1 = times[
        index
    ]

    if target == t0:
        return state_from_row(
            row0
        )

    if target == t1:
        return state_from_row(
            row1
        )

    dt = (
        t1 - t0
    ).total_seconds()

    u = (
        target - t0
    ).total_seconds() / dt

    p0, v0 = state_from_row(
        row0
    )

    p1, v1 = state_from_row(
        row1
    )

    h00 = (
        2 * u**3
        - 3 * u**2
        + 1
    )

    h10 = (
        u**3
        - 2 * u**2
        + u
    )

    h01 = (
        -2 * u**3
        + 3 * u**2
    )

    h11 = (
        u**3
        - u**2
    )

    p = [
        (
            h00 * p0[i]
            + h10 * dt * v0[i]
            + h01 * p1[i]
            + h11 * dt * v1[i]
        )
        for i in range(3)
    ]

    dh00 = (
        6 * u**2
        - 6 * u
    )

    dh10 = (
        3 * u**2
        - 4 * u
        + 1
    )

    dh01 = (
        -6 * u**2
        + 6 * u
    )

    dh11 = (
        3 * u**2
        - 2 * u
    )

    v = [
        (
            dh00 * p0[i]
            + dh10 * dt * v0[i]
            + dh01 * p1[i]
            + dh11 * dt * v1[i]
        )
        / dt
        for i in range(3)
    ]

    return (
        p,
        v,
    )


def main():
    reference = load_json(
        REFERENCE_PATH
    )

    mission_config = load_json(
        MISSION_CONFIG_PATH
    )

    maneuver_reference = load_json(
        MANEUVER_PATH
    )

    propulsion_reference = load_json(
        PROPULSION_PATH
    )

    phase = load_json(
        MISSION_PHASE_PATH
    )

    entry_reference = load_json(
        ENTRY_EVENTS_PATH
    )

    communications = load_json(
        COMMUNICATIONS_PATH
    )

    manifest = load_json(
        MANIFEST_PATH
    )

    summary = load_json(
        SUMMARY_PATH
    )

    if (
        reference[
            "dataset_id"
        ]
        != EXPECTED_DATASET_ID
    ):
        fail(
            "reference dataset ID mismatch"
        )

    if (
        summary[
            "product_id"
        ]
        != EXPECTED_PRODUCT_ID
    ):
        fail(
            "summary product ID mismatch"
        )

    if (
        mission_config[
            "launch_epoch_utc"
        ]
        != "2026-04-01T22:35:12Z"
    ):
        fail(
            "launch epoch changed"
        )

    anchors = (
        reference[
            "mission_anchors"
        ]
    )

    expected_anchor_values = {
        "lunar_soi_entry":
            phase[
                "lunar_soi"
            ][
                "derived_entry_utc"
            ],

        "pericynthion":
            phase[
                "pericynthion"
            ][
                "timestamp_utc"
            ],

        "lunar_soi_exit":
            phase[
                "lunar_soi"
            ][
                "derived_exit_utc"
            ],
    }

    for key, observed in (
        expected_anchor_values.items()
    ):
        if (
            parse_utc(
                anchors[
                    key
                ][
                    "timestamp_utc"
                ]
            )
            != parse_utc(
                observed
            )
        ):
            fail(
                f"{key} mismatch"
            )

    entry_events = {
        event[
            "event_id"
        ]:
            event
        for event in entry_reference[
            "events"
        ]
    }

    if (
        anchors[
            "entry_interface"
        ][
            "timestamp_utc"
        ]
        != entry_events[
            "entry_interface"
        ][
            "reported_utc_minute"
        ]
    ):
        fail(
            "Entry Interface anchor mismatch"
        )

    if (
        anchors[
            "splashdown"
        ][
            "timestamp_utc"
        ]
        != entry_events[
            "splashdown"
        ][
            "reported_utc_minute"
        ]
    ):
        fail(
            "splashdown anchor mismatch"
        )

    if (
        anchors[
            "entry_interface"
        ][
            "precision"
        ]
        != "MINUTE_LEVEL"
        or anchors[
            "splashdown"
        ][
            "precision"
        ]
        != "MINUTE_LEVEL"
    ):
        fail(
            "entry-event precision changed"
        )

    comms = {
        event[
            "id"
        ]:
            event
        for event in communications[
            "events"
        ]
    }

    loss = (
        comms[
            "unexpected_return_link_loss"
        ]
    )

    if (
        loss[
            "precision"
        ]
        != "APPROXIMATE"
        or loss[
            "anchor_is_not_exact"
        ]
        is not True
    ):
        fail(
            "RTC2 anomaly precision boundary failed"
        )

    maneuvers = {
        item[
            "maneuver_id"
        ]:
            item
        for item in maneuver_reference[
            "maneuvers"
        ]
    }

    assignments = {
        item[
            "maneuver_id"
        ]:
            item
        for item in propulsion_reference[
            "correction_burn_assignments"
        ]
    }

    correlation_rows = (
        reference[
            "maneuver_correlations"
        ]
    )

    if [
        item[
            "maneuver_id"
        ]
        for item in correlation_rows
    ] != BURN_IDS:
        fail(
            "maneuver correlation order changed"
        )

    expected_burn_values = {
        "otc3": (
            "2026-04-06T03:03:00Z",
            "04:04:27:48.000",
            "OUTBOUND_TRANSIT",
            17.5,
            None,
        ),
        "rtc1": (
            "2026-04-08T00:03:00Z",
            "06:01:27:48.000",
            "TRANS_EARTH_RETURN",
            15.0,
            1.6,
        ),
        "rtc2": (
            "2026-04-10T02:53:00Z",
            "08:04:17:48.000",
            "TRANS_EARTH_RETURN",
            9.0,
            5.3,
        ),
        "rtc3": (
            "2026-04-10T18:53:00Z",
            "08:20:17:48.000",
            "TRANS_EARTH_RETURN",
            8.0,
            4.2,
        ),
    }

    for row in correlation_rows:
        maneuver_id = (
            row[
                "maneuver_id"
            ]
        )

        (
            timestamp,
            met,
            mission_phase,
            duration,
            delta_v,
        ) = expected_burn_values[
            maneuver_id
        ]

        if (
            row[
                "timestamp_utc"
            ]
            != timestamp
            or row[
                "timestamp_precision"
            ]
            != "MINUTE_LEVEL"
            or row[
                "met_anchor"
            ]
            != met
            or row[
                "geometric_mission_phase"
            ]
            != mission_phase
        ):
            fail(
                f"{maneuver_id} clock/phase metadata changed"
            )

        check_close(
            f"{maneuver_id} duration",
            row[
                "duration_seconds"
            ],
            duration,
        )

        if delta_v is None:
            if (
                row[
                    "reported_delta_v_ft_s"
                ]
                is not None
            ):
                fail(
                    "OTC3 gained unsupported delta-v"
                )
        else:
            check_close(
                f"{maneuver_id} delta-v",
                row[
                    "reported_delta_v_ft_s"
                ],
                delta_v,
            )

        execution = (
            maneuvers[
                maneuver_id
            ][
                "execution"
            ]
        )

        if (
            execution[
                "timestamp_utc"
            ]
            != timestamp
        ):
            fail(
                f"{maneuver_id} Phase 2I.1 timestamp changed"
            )

        if (
            assignments[
                maneuver_id
            ][
                "assignment_status"
            ]
            != "UNRESOLVED_AS_FLOWN"
            or assignments[
                maneuver_id
            ][
                "as_flown_engine_class_id"
            ]
            is not None
        ):
            fail(
                f"{maneuver_id} engine assignment "
                "incorrectly resolved"
            )

    interval_expected = {
        "otc3_to_lunar_soi_entry":
            5707.532302,

        "otc3_to_pericynthion":
            71866.177998,

        "lunar_soi_exit_to_rtc1":
            23958.077789,

        "rtc1_to_rtc2":
            183000.0,

        "rtc2_to_rtc3":
            57600.0,

        "rtc3_to_entry_interface":
            18000.0,

        "rtc3_to_splashdown":
            18840.0,

        "rtc2_loss_anchor_to_rtc2":
            7200.0,
    }

    for key, expected in (
        interval_expected.items()
    ):
        check_close(
            key,
            summary[
                "mission_clock"
            ][
                "intervals_seconds"
            ][
                key
            ],
            expected,
        )

    if (
        summary[
            "rtc2_communications_context"
        ][
            "precision"
        ]
        != "APPROXIMATE"
        or summary[
            "rtc2_communications_context"
        ][
            "anchor_is_not_exact"
        ]
        is not True
    ):
        fail(
            "summary RTC2 anomaly precision changed"
        )

    if len(
        manifest
    ) != 9:
        fail(
            "standard OEM product count changed"
        )

    products = {}

    for item in manifest:
        product_path = Path(
            item[
                "output_csv"
            ]
        )

        if not product_path.is_absolute():
            product_path = (
                ROOT
                / product_path
            )

        metadata_path = Path(
            item[
                "metadata_file"
            ]
        )

        if not metadata_path.is_absolute():
            metadata_path = (
                ROOT
                / metadata_path
            )

        metadata = load_json(
            metadata_path
        )

        rows, times = load_product(
            product_path
        )

        products[
            product_path.name
        ] = {
            "creation":
                parse_utc(
                    metadata[
                        "CREATION_DATE"
                    ]
                ),

            "rows":
                rows,

            "times":
                times,
        }

    brackets = {
        item[
            "maneuver_id"
        ]:
            item
        for item in reference[
            "oem_creation_time_brackets"
        ]
    }

    expected_pairs = {
        "otc3": (
            "Artemis_II_OEM_2026_04_04_to_EI.csv",
            "Artemis_II_OEM_2026_04_06_Pre-OTC3_to_EI.csv",
            169.098527,
            1.893541,
        ),
        "rtc1": (
            "Artemis_II_OEM_2026_04_07_Pre-Lunar-Flyby_to_EI.csv",
            "Artemis_II_OEM_2026_04_08_Post-ICPS-Sep_to_EI.csv",
            1.443975,
            0.068048,
        ),
        "rtc2": (
            "Artemis_II_OEM_2026_04_09_Post-ICPS-Sep_to_EI.csv",
            "Artemis_II_OEM_2026_04_10_Post-ICPS-Sep-to-EI.csv",
            34.536691,
            0.381837,
        ),
        "rtc3": (
            "Artemis_II_OEM_2026_04_10_Post-ICPS-Sep-to-EI.csv",
            None,
            None,
            None,
        ),
    }

    burn_times = {
        maneuver_id:
            parse_utc(
                maneuvers[
                    maneuver_id
                ][
                    "execution"
                ][
                    "timestamp_utc"
                ]
            )
        for maneuver_id in BURN_IDS
    }

    for maneuver_id, expected in (
        expected_pairs.items()
    ):
        (
            before_name,
            after_name,
            expected_position,
            expected_velocity,
        ) = expected

        bracket = (
            brackets[
                maneuver_id
            ]
        )

        if (
            bracket[
                "latest_product_created_at_or_before_maneuver"
            ][
                "product"
            ]
            != before_name
        ):
            fail(
                f"{maneuver_id} before-product changed"
            )

        if (
            bracket[
                "maneuver_assimilation_status"
            ]
            != "NOT_ESTABLISHED"
        ):
            fail(
                f"{maneuver_id} assimilation incorrectly established"
            )

        difference = (
            bracket[
                "same_epoch_solution_difference"
            ]
        )

        if (
            difference[
                "measured_burn_delta_v"
            ]
            is not False
            or difference[
                "navigation_error"
            ]
            is not False
        ):
            fail(
                f"{maneuver_id} OEM interpretation boundary failed"
            )

        if after_name is None:
            if (
                bracket[
                    "earliest_product_created_after_maneuver"
                ]
                is not None
            ):
                fail(
                    "RTC3 unexpectedly gained a later OEM"
                )

            if (
                difference[
                    "available"
                ]
                is not False
            ):
                fail(
                    "RTC3 comparison incorrectly marked available"
                )

            continue

        if (
            bracket[
                "earliest_product_created_after_maneuver"
            ][
                "product"
            ]
            != after_name
        ):
            fail(
                f"{maneuver_id} after-product changed"
            )

        burn_time = (
            burn_times[
                maneuver_id
            ]
        )

        before_product = (
            products[
                before_name
            ]
        )

        after_product = (
            products[
                after_name
            ]
        )

        before_state = interpolate_state(
            before_product[
                "rows"
            ],
            before_product[
                "times"
            ],
            burn_time,
        )

        after_state = interpolate_state(
            after_product[
                "rows"
            ],
            after_product[
                "times"
            ],
            burn_time,
        )

        if (
            before_state is None
            or after_state is None
        ):
            fail(
                f"{maneuver_id} common-epoch state unavailable"
            )

        p0, v0 = before_state
        p1, v1 = after_state

        position_difference = magnitude(
            [
                p1[i] - p0[i]
                for i in range(3)
            ]
        )

        velocity_difference = (
            magnitude(
                [
                    v1[i] - v0[i]
                    for i in range(3)
                ]
            )
            * 1000.0
        )

        check_close(
            f"{maneuver_id} recomputed position difference",
            position_difference,
            expected_position,
            tolerance=5e-6,
        )

        check_close(
            f"{maneuver_id} recomputed velocity difference",
            velocity_difference,
            expected_velocity,
            tolerance=5e-6,
        )

        check_close(
            f"{maneuver_id} reference position difference",
            difference[
                "position_difference_km"
            ],
            expected_position,
            tolerance=5e-6,
        )

        check_close(
            f"{maneuver_id} reference velocity difference",
            difference[
                "velocity_difference_m_s"
            ],
            expected_velocity,
            tolerance=5e-6,
        )

    otc3_after = (
        brackets[
            "otc3"
        ][
            "earliest_product_created_after_maneuver"
        ]
    )

    if (
        "PRE_OTC3"
        not in otc3_after[
            "filename_semantics"
        ]
    ):
        fail(
            "OTC3 PRE_OTC3 audit evidence lost"
        )

    audit = (
        reference[
            "oem_metadata_audit"
        ]
    )

    if (
        audit[
            "explicit_maneuver_assimilation_field_observed"
        ]
        is not False
        or audit[
            "creation_date_establishes_maneuver_assimilation"
        ]
        is not False
        or audit[
            "filename_semantics_establish_as_flown_state"
        ]
        is not False
    ):
        fail(
            "OEM assimilation audit boundary changed"
        )

    boundary = (
        reference[
            "analysis_boundary"
        ]
    )

    if (
        boundary[
            "public_oem_solution_evolution_allowed"
        ]
        is not True
        or boundary[
            "oem_state_difference_as_measured_burn_delta_v_allowed"
        ]
        is not False
        or boundary[
            "oem_state_difference_as_navigation_error_allowed"
        ]
        is not False
        or boundary[
            "thrust_derived_correction_performance_allowed"
        ]
        is not False
        or boundary[
            "burn_impulse_from_nominal_thrust_allowed"
        ]
        is not False
    ):
        fail(
            "analysis boundary changed"
        )

    if not MISSION_CLOCK_CSV.exists():
        fail(
            "mission-clock CSV missing"
        )

    with MISSION_CLOCK_CSV.open(
        "r",
        encoding="utf-8-sig",
    ) as f:
        mission_rows = list(
            csv.DictReader(f)
        )

    if len(
        mission_rows
    ) != 4:
        fail(
            "mission-clock CSV must contain four rows"
        )

    if [
        row[
            "maneuver_id"
        ]
        for row in mission_rows
    ] != BURN_IDS:
        fail(
            "mission-clock CSV maneuver order changed"
        )

    if not OEM_BRACKET_CSV.exists():
        fail(
            "OEM bracket CSV missing"
        )

    with OEM_BRACKET_CSV.open(
        "r",
        encoding="utf-8-sig",
    ) as f:
        bracket_rows = list(
            csv.DictReader(f)
        )

    if len(
        bracket_rows
    ) != 4:
        fail(
            "OEM bracket CSV must contain four rows"
        )

    for row in bracket_rows:
        if (
            row[
                "maneuver_assimilation_status"
            ]
            != "NOT_ESTABLISHED"
            or row[
                "measured_burn_delta_v"
            ]
            != "false"
            or row[
                "navigation_error"
            ]
            != "false"
        ):
            fail(
                "OEM CSV interpretation boundary failed"
            )

    if (
        summary[
            "oem_archive"
        ][
            "standard_product_count"
        ]
        != 9
        or summary[
            "oem_archive"
        ][
            "creation_date_establishes_maneuver_assimilation"
        ]
        is not False
    ):
        fail(
            "summary OEM audit changed"
        )

    if (
        summary[
            "analysis_boundary"
        ]
        != boundary
    ):
        fail(
            "summary analysis boundary mismatch"
        )

    if (
        summary[
            "guardrails"
        ]
        != reference[
            "guardrails"
        ]
    ):
        fail(
            "summary guardrails mismatch"
        )

    for figure in [
        MISSION_CLOCK_FIGURE,
        OEM_BRACKET_FIGURE,
    ]:
        if not figure.exists():
            fail(
                f"missing figure: {figure}"
            )

        svg = figure.read_text(
            encoding="utf-8"
        )

        if (
            "<svg" not in svg
            or len(svg) < 1000
        ):
            fail(
                f"invalid SVG: {figure}"
            )

    print()
    print(
        "Phase 2I.3 Maneuver Mission-Clock / "
        "Trajectory-Solution Validation"
    )

    print("=" * 74)

    print()
    print(
        "Mission-clock maneuvers:"
    )

    print(
        "  OTC3: OUTBOUND_TRANSIT"
    )

    print(
        "  RTC1: TRANS_EARTH_RETURN"
    )

    print(
        "  RTC2: TRANS_EARTH_RETURN"
    )

    print(
        "  RTC3: TRANS_EARTH_RETURN"
    )

    print()
    print(
        "Mission-event intervals:"
    )

    print(
        "  OTC3 -> SOI entry:"
    )

    print(
        "    5707.532302 s"
    )

    print(
        "  OTC3 -> pericynthion:"
    )

    print(
        "    71866.177998 s"
    )

    print(
        "  SOI exit -> RTC1:"
    )

    print(
        "    23958.077789 s"
    )

    print(
        "  RTC1 -> RTC2:"
    )

    print(
        "    183000.0 s"
    )

    print(
        "  RTC2 -> RTC3:"
    )

    print(
        "    57600.0 s"
    )

    print(
        "  RTC3 -> Entry Interface:"
    )

    print(
        "    18000.0 s"
    )

    print(
        "  RTC3 -> splashdown:"
    )

    print(
        "    18840.0 s"
    )

    print(
        "  approximate loss anchor -> RTC2:"
    )

    print(
        "    ~7200.0 s"
    )

    print()
    print(
        "OEM archive:"
    )

    print(
        "  standard products: 9"
    )

    print(
        "  explicit maneuver-assimilation field:"
    )

    print(
        "    NONE"
    )

    print(
        "  CREATION_DATE proves assimilation:"
    )

    print(
        "    FALSE"
    )

    print()
    print(
        "Same-epoch public OEM solution differences:"
    )

    print(
        "  OTC3:"
    )

    print(
        "    169.098527 km"
    )

    print(
        "    1.893541 m/s"
    )

    print(
        "    assimilation: NOT_ESTABLISHED"
    )

    print(
        "  RTC1:"
    )

    print(
        "    1.443975 km"
    )

    print(
        "    0.068048 m/s"
    )

    print(
        "    assimilation: NOT_ESTABLISHED"
    )

    print(
        "  RTC2:"
    )

    print(
        "    34.536691 km"
    )

    print(
        "    0.381837 m/s"
    )

    print(
        "    assimilation: NOT_ESTABLISHED"
    )

    print(
        "  RTC3:"
    )

    print(
        "    later public OEM: NONE"
    )

    print(
        "    direct comparison: NOT AVAILABLE"
    )

    print()
    print(
        "OTC3 audit:"
    )

    print(
        "  later-created OEM label: PRE_OTC3"
    )

    print(
        "  creation time proves maneuver assimilation: FALSE"
    )

    print()
    print(
        "Interpretation boundary:"
    )

    print(
        "  OEM difference = solution-to-solution: PASS"
    )

    print(
        "  OEM difference = navigation error: FALSE"
    )

    print(
        "  OEM difference = measured burn delta-v: FALSE"
    )

    print(
        "  unresolved engine assignments preserved: PASS"
    )

    print(
        "  thrust-derived burn performance computed: FALSE"
    )

    print(
        "  nominal-thrust burn impulse computed: FALSE"
    )

    print()
    print(
        "Products:"
    )

    print(
        "  mission-clock CSV rows: 4"
    )

    print(
        "  OEM bracket CSV rows: 4"
    )

    print(
        "  summary: PASS"
    )

    print(
        "  mission-clock figure: PASS"
    )

    print(
        "  OEM bracket figure: PASS"
    )

    print()
    print(
        "OK: Phase 2I.3 maneuver mission-clock correlation, "
        "geometric mission-phase classification, entry and "
        "communications timing boundaries, OEM creation-time "
        "brackets, independent common-epoch state comparisons, "
        "OTC3 PRE-OTC3 metadata contradiction handling, "
        "maneuver-assimilation uncertainty, unresolved propulsion "
        "assignments, generated products, and non-telemetry "
        "interpretation guardrails independently validated."
    )


if __name__ == "__main__":
    main()