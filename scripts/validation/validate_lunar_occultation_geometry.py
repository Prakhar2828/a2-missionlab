from __future__ import annotations

import csv
import json
import math
from bisect import bisect_right
from datetime import datetime, timedelta, timezone
from pathlib import Path

import spiceypy as spice


ROOT = Path(__file__).resolve().parents[2]

TRAJECTORY_PATH = (
    ROOT
    / "data"
    / "processed"
    / "trajectory"
    / "primary_trajectory.csv"
)

TRAJECTORY_EVENTS_PATH = (
    ROOT
    / "data"
    / "reference"
    / "trajectory_events.json"
)

REFERENCE_PATH = (
    ROOT
    / "data"
    / "reference"
    / "artemis_ii_communications_events.json"
)

OUTPUT_CSV = (
    ROOT
    / "data"
    / "processed"
    / "communications"
    / "lunar_occultation_geometry.csv"
)

SUMMARY_PATH = (
    ROOT
    / "data"
    / "processed"
    / "communications"
    / "lunar_occultation_summary.json"
)

FIGURE_PATH = (
    ROOT
    / "docs"
    / "assets"
    / "communications"
    / "phase2g_lunar_occultation_geometry.svg"
)

SPICE_DIR = (
    ROOT
    / "data"
    / "raw"
    / "spice"
)

EXPECTED_REFERENCE_ID = (
    "phase2g1_artemis_ii_communications_reference"
)

EXPECTED_PRODUCT_ID = (
    "phase2g1_geocentric_lunar_occultation"
)

EXPECTED_PROVENANCE = (
    "MISSIONLAB_DERIVED_GEOMETRY_"
    "WITH_NASA_REPORTED_VALIDATION_REFERENCE"
)


def fail(
    message: str,
) -> None:
    raise SystemExit(
        "VALIDATION FAILED: "
        f"{message}"
    )


def load_json(
    path: Path,
):
    if not path.exists():
        fail(
            f"missing required file: {path}"
        )

    with path.open(
        "r",
        encoding="utf-8-sig",
    ) as f:
        return json.load(f)


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


def spice_time_string(
    timestamp: datetime,
) -> str:
    return (
        timestamp.astimezone(
            timezone.utc
        ).strftime(
            "%Y-%m-%d %H:%M:%S.%f"
        )
        + " UTC"
    )


def dot(
    a,
    b,
):
    return sum(
        x * y
        for x, y in zip(a, b)
    )


def norm(
    vector,
):
    return math.sqrt(
        dot(
            vector,
            vector,
        )
    )


def load_trajectory():
    rows = []

    if not TRAJECTORY_PATH.exists():
        fail(
            "missing primary trajectory"
        )

    with TRAJECTORY_PATH.open(
        "r",
        encoding="utf-8-sig",
    ) as f:
        reader = csv.DictReader(
            f
        )

        for row in reader:
            rows.append(
                {
                    "timestamp":
                        parse_utc(
                            row[
                                "timestamp_utc"
                            ]
                        ),

                    "position": [
                        float(
                            row[
                                "x_km"
                            ]
                        ),
                        float(
                            row[
                                "y_km"
                            ]
                        ),
                        float(
                            row[
                                "z_km"
                            ]
                        ),
                    ],

                    "velocity": [
                        float(
                            row[
                                "vx_km_s"
                            ]
                        ),
                        float(
                            row[
                                "vy_km_s"
                            ]
                        ),
                        float(
                            row[
                                "vz_km_s"
                            ]
                        ),
                    ],
                }
            )

    rows.sort(
        key=lambda row:
            row[
                "timestamp"
            ]
    )

    if len(rows) != 3262:
        fail(
            "expected 3262 primary "
            "trajectory states"
        )

    return rows


def hermite(
    row0,
    row1,
    timestamp,
):
    dt = (
        row1[
            "timestamp"
        ]
        - row0[
            "timestamp"
        ]
    ).total_seconds()

    elapsed = (
        timestamp
        - row0[
            "timestamp"
        ]
    ).total_seconds()

    s = (
        elapsed / dt
    )

    s = max(
        0.0,
        min(
            1.0,
            s,
        ),
    )

    h00 = (
        2.0 * s**3
        - 3.0 * s**2
        + 1.0
    )

    h10 = (
        s**3
        - 2.0 * s**2
        + s
    )

    h01 = (
        -2.0 * s**3
        + 3.0 * s**2
    )

    h11 = (
        s**3
        - s**2
    )

    return [
        (
            h00
            * row0[
                "position"
            ][i]
            + h10
            * dt
            * row0[
                "velocity"
            ][i]
            + h01
            * row1[
                "position"
            ][i]
            + h11
            * dt
            * row1[
                "velocity"
            ][i]
        )
        for i in range(3)
    ]


class IndependentModel:
    def __init__(
        self,
        rows,
        moon_radius,
    ):
        self.rows = rows

        self.times = [
            row[
                "timestamp"
            ]
            for row in rows
        ]

        self.moon_radius = (
            moon_radius
        )

    def orion(
        self,
        timestamp,
    ):
        index = (
            bisect_right(
                self.times,
                timestamp,
            )
            - 1
        )

        index = max(
            0,
            min(
                len(self.rows) - 2,
                index,
            ),
        )

        return hermite(
            self.rows[index],
            self.rows[index + 1],
            timestamp,
        )

    def geometry(
        self,
        timestamp,
        position=None,
    ):
        if position is None:
            position = self.orion(
                timestamp
            )

        et = spice.str2et(
            spice_time_string(
                timestamp
            )
        )

        moon_state, _ = spice.spkezr(
            "MOON",
            et,
            "J2000",
            "NONE",
            "EARTH",
        )

        moon = [
            float(
                moon_state[i]
            )
            for i in range(3)
        ]

        parameter = (
            dot(
                moon,
                position,
            )
            / dot(
                position,
                position,
            )
        )

        closest = [
            parameter
            * position[i]
            for i in range(3)
        ]

        offset = [
            moon[i]
            - closest[i]
            for i in range(3)
        ]

        center_distance = (
            norm(offset)
        )

        clearance = (
            center_distance
            - self.moon_radius
        )

        moon_between = (
            0.0
            < parameter
            < 1.0
        )

        return {
            "clearance":
                clearance,

            "moon_between":
                moon_between,

            "occulted":
                (
                    moon_between
                    and clearance < 0.0
                ),

            "orion_range":
                norm(position),

            "center_distance":
                center_distance,

            "projection":
                parameter,
        }


def refine_root(
    model,
    left,
    right,
):
    fl = model.geometry(
        left
    )[
        "clearance"
    ]

    fr = model.geometry(
        right
    )[
        "clearance"
    ]

    if fl * fr > 0.0:
        fail(
            "independent contact bracket "
            "does not contain a root"
        )

    for _ in range(80):
        width = (
            right - left
        ).total_seconds()

        if width < 1e-6:
            break

        middle = (
            left
            + timedelta(
                seconds=(
                    width / 2.0
                )
            )
        )

        fm = model.geometry(
            middle
        )[
            "clearance"
        ]

        if (
            fl * fm
            <= 0.0
        ):
            right = middle
            fr = fm

        else:
            left = middle
            fl = fm

    return (
        left
        + timedelta(
            seconds=(
                (
                    right - left
                ).total_seconds()
                / 2.0
            )
        )
    )


def overlap_fraction(
    a0,
    a1,
    b0,
    b1,
):
    intersection = max(
        0.0,
        (
            min(
                a1,
                b1,
            )
            - max(
                a0,
                b0,
            )
        ).total_seconds(),
    )

    union = (
        max(
            a1,
            b1,
        )
        - min(
            a0,
            b0,
        )
    ).total_seconds()

    return (
        intersection / union
    )


def main() -> None:
    reference = load_json(
        REFERENCE_PATH
    )

    summary = load_json(
        SUMMARY_PATH
    )

    if (
        reference.get(
            "dataset_id"
        )
        != EXPECTED_REFERENCE_ID
    ):
        fail(
            "unexpected communications "
            "reference dataset ID"
        )

    if (
        reference.get(
            "provenance"
        )
        != "NASA_REPORTED"
    ):
        fail(
            "unexpected communications "
            "reference provenance"
        )

    public_window = (
        reference[
            "public_lunar_occultation_window"
        ]
    )

    nasa_los = parse_utc(
        public_window[
            "loss_of_signal_utc"
        ]
    )

    nasa_aos = parse_utc(
        public_window[
            "acquisition_of_signal_utc"
        ]
    )

    if (
        nasa_los
        != datetime(
            2026,
            4,
            6,
            22,
            44,
            tzinfo=timezone.utc,
        )
    ):
        fail(
            "NASA LOS reference changed"
        )

    if (
        nasa_aos
        != datetime(
            2026,
            4,
            6,
            23,
            25,
            tzinfo=timezone.utc,
        )
    ):
        fail(
            "NASA AOS reference changed"
        )

    if (
        public_window.get(
            "exact_signal_threshold_measurement"
        )
        is not False
    ):
        fail(
            "NASA public timing must not "
            "be classified as an exact "
            "signal-threshold measurement"
        )

    model_reference = (
        reference[
            "phase2g1_geometric_model"
        ]
    )

    if (
        model_reference.get(
            "observer"
        )
        != "EARTH_CENTER"
    ):
        fail(
            "Phase 2G.1 observer changed"
        )

    if (
        model_reference.get(
            "aberration_correction"
        )
        != "NONE"
    ):
        fail(
            "Phase 2G.1 aberration "
            "assumption changed"
        )

    thresholds = (
        reference[
            "validation_thresholds"
        ]
    )

    trajectory = load_trajectory()

    kernels = [
        SPICE_DIR
        / "naif0012.tls",

        SPICE_DIR
        / "de440s.bsp",

        SPICE_DIR
        / "pck00011.tpc",
    ]

    try:
        for kernel in kernels:
            if not kernel.exists():
                fail(
                    f"missing SPICE kernel: {kernel}"
                )

            spice.furnsh(
                str(kernel)
            )

        _, radii = spice.bodvrd(
            "MOON",
            "RADII",
            3,
        )

        moon_radius = float(
            sum(radii)
            / 3.0
        )

        model = IndependentModel(
            trajectory,
            moon_radius,
        )

        samples = []

        for row in trajectory:
            geometry = (
                model.geometry(
                    row[
                        "timestamp"
                    ],
                    position=(
                        row[
                            "position"
                        ]
                    ),
                )
            )

            samples.append(
                {
                    "timestamp":
                        row[
                            "timestamp"
                        ],

                    **geometry,
                }
            )

        brackets = []

        for a, b in zip(
            samples[:-1],
            samples[1:],
        ):
            if (
                a[
                    "moon_between"
                ]
                and b[
                    "moon_between"
                ]
                and (
                    a[
                        "clearance"
                    ]
                    * b[
                        "clearance"
                    ]
                    < 0.0
                )
            ):
                brackets.append(
                    (
                        a[
                            "timestamp"
                        ],
                        b[
                            "timestamp"
                        ],
                    )
                )

        if len(brackets) != 2:
            fail(
                "expected exactly two "
                "independent occultation "
                "contact brackets"
            )

        ingress = refine_root(
            model,
            brackets[0][0],
            brackets[0][1],
        )

        egress = refine_root(
            model,
            brackets[1][0],
            brackets[1][1],
        )

        duration = (
            egress - ingress
        ).total_seconds()

        nasa_duration = (
            nasa_aos
            - nasa_los
        ).total_seconds()

        ingress_offset = (
            ingress
            - nasa_los
        ).total_seconds()

        egress_offset = (
            egress
            - nasa_aos
        ).total_seconds()

        duration_difference = (
            duration
            - nasa_duration
        )

        overlap = overlap_fraction(
            ingress,
            egress,
            nasa_los,
            nasa_aos,
        )

        max_contact_offset = float(
            thresholds[
                "maximum_absolute_contact_offset_from_public_nasa_time_seconds"
            ]
        )

        if abs(
            ingress_offset
        ) > max_contact_offset:
            fail(
                "geocentric ingress is "
                "too far from NASA public LOS"
            )

        if abs(
            egress_offset
        ) > max_contact_offset:
            fail(
                "geocentric egress is "
                "too far from NASA public AOS"
            )

        if abs(
            duration_difference
        ) > float(
            thresholds[
                "maximum_absolute_duration_difference_seconds"
            ]
        ):
            fail(
                "geocentric occultation "
                "duration is inconsistent "
                "with NASA public window"
            )

        if overlap < float(
            thresholds[
                "minimum_window_overlap_fraction"
            ]
        ):
            fail(
                "geocentric and NASA public "
                "windows overlap too little"
            )

        duration_minutes = (
            duration / 60.0
        )

        if duration_minutes < float(
            thresholds[
                "minimum_expected_duration_minutes"
            ]
        ):
            fail(
                "occultation duration "
                "unexpectedly short"
            )

        if duration_minutes > float(
            thresholds[
                "maximum_expected_duration_minutes"
            ]
        ):
            fail(
                "occultation duration "
                "unexpectedly long"
            )

        trajectory_events = load_json(
            TRAJECTORY_EVENTS_PATH
        )

        pericynthion_matches = [
            event
            for event in trajectory_events
            if event.get("id")
            == "pericynthion"
        ]

        if len(
            pericynthion_matches
        ) != 1:
            fail(
                "expected one pericynthion "
                "reference event"
            )

        pericynthion = parse_utc(
            pericynthion_matches[0][
                "timestamp_utc"
            ]
        )

        pericynthion_geometry = (
            model.geometry(
                pericynthion
            )
        )

        if not (
            ingress
            < pericynthion
            < egress
        ):
            fail(
                "refined pericynthion is not "
                "inside derived occultation"
            )

        if not pericynthion_geometry[
            "occulted"
        ]:
            fail(
                "pericynthion geometry is not "
                "classified as occulted"
            )

        if (
            summary.get(
                "product_id"
            )
            != EXPECTED_PRODUCT_ID
        ):
            fail(
                "unexpected summary product ID"
            )

        if (
            summary.get(
                "provenance"
            )
            != EXPECTED_PROVENANCE
        ):
            fail(
                "unexpected summary provenance"
            )

        if (
            summary.get(
                "reference_dataset_id"
            )
            != EXPECTED_REFERENCE_ID
        ):
            fail(
                "summary reference dataset "
                "does not match"
            )

        summary_model = (
            summary[
                "model"
            ]
        )

        if abs(
            float(
                summary_model[
                    "moon_mean_radius_km"
                ]
            )
            - moon_radius
        ) > 1e-9:
            fail(
                "summary Moon radius "
                "does not match SPICE"
            )

        summary_window = (
            summary[
                "geocentric_occultation_window"
            ]
        )

        summary_ingress = parse_utc(
            summary_window[
                "ingress_utc"
            ]
        )

        summary_egress = parse_utc(
            summary_window[
                "egress_utc"
            ]
        )

        if abs(
            (
                summary_ingress
                - ingress
            ).total_seconds()
        ) > 0.001:
            fail(
                "summary ingress does not "
                "match independent reconstruction"
            )

        if abs(
            (
                summary_egress
                - egress
            ).total_seconds()
        ) > 0.001:
            fail(
                "summary egress does not "
                "match independent reconstruction"
            )

        if abs(
            float(
                summary_window[
                    "duration_seconds"
                ]
            )
            - duration
        ) > 0.001:
            fail(
                "summary duration does not "
                "match independent reconstruction"
            )

        nasa_comparison = (
            summary[
                "nasa_comparison"
            ]
        )

        if abs(
            float(
                nasa_comparison[
                    "ingress_minus_nasa_los_seconds"
                ]
            )
            - ingress_offset
        ) > 0.001:
            fail(
                "summary ingress offset mismatch"
            )

        if abs(
            float(
                nasa_comparison[
                    "egress_minus_nasa_aos_seconds"
                ]
            )
            - egress_offset
        ) > 0.001:
            fail(
                "summary egress offset mismatch"
            )

        if abs(
            float(
                nasa_comparison[
                    "window_overlap_fraction"
                ]
            )
            - overlap
        ) > 1e-9:
            fail(
                "summary window overlap mismatch"
            )

        pericynthion_summary = (
            summary[
                "pericynthion_context"
            ]
        )

        if (
            pericynthion_summary.get(
                "inside_geocentric_occultation"
            )
            is not True
        ):
            fail(
                "summary pericynthion "
                "inside-window flag false"
            )

        if (
            pericynthion_summary.get(
                "geometrically_occulted"
            )
            is not True
        ):
            fail(
                "summary pericynthion "
                "occultation flag false"
            )

        if (
            summary.get(
                "guardrails"
            )
            != reference.get(
                "guardrails"
            )
        ):
            fail(
                "summary guardrails changed"
            )

        if not OUTPUT_CSV.exists():
            fail(
                "missing sampled geometry CSV"
            )

        with OUTPUT_CSV.open(
            "r",
            encoding="utf-8-sig",
        ) as f:
            output_rows = list(
                csv.DictReader(f)
            )

        if len(output_rows) != 3262:
            fail(
                "sampled communications "
                "geometry CSV does not contain "
                "3262 rows"
            )

        if not FIGURE_PATH.exists():
            fail(
                "missing communications SVG"
            )

        svg = FIGURE_PATH.read_text(
            encoding="utf-8",
        )

        if "<svg" not in svg:
            fail(
                "invalid communications SVG"
            )

        if len(svg) < 1000:
            fail(
                "communications SVG "
                "unexpectedly small"
            )

        print()
        print(
            "Phase 2G.1 Geocentric Lunar "
            "Occultation Validation"
        )

        print(
            "=" * 55
        )

        print()
        print(
            "Independent geometric contacts:"
        )

        print(
            "  ingress / LOS:"
        )

        print(
            "    "
            f"{ingress.isoformat()}"
        )

        print(
            "  egress / AOS:"
        )

        print(
            "    "
            f"{egress.isoformat()}"
        )

        print(
            "  duration:"
        )

        print(
            f"    "
            f"{duration:.3f} s"
        )

        print(
            f"    "
            f"{duration_minutes:.3f} min"
        )

        print()
        print(
            "NASA public window:"
        )

        print(
            "  LOS:"
        )

        print(
            "    "
            f"{nasa_los.isoformat()}"
        )

        print(
            "  AOS:"
        )

        print(
            "    "
            f"{nasa_aos.isoformat()}"
        )

        print()
        print(
            "Consistency:"
        )

        print(
            "  ingress offset:"
        )

        print(
            f"    "
            f"{ingress_offset:+.3f} s"
        )

        print(
            "  egress offset:"
        )

        print(
            f"    "
            f"{egress_offset:+.3f} s"
        )

        print(
            "  duration difference:"
        )

        print(
            f"    "
            f"{duration_difference:+.3f} s"
        )

        print(
            "  window overlap:"
        )

        print(
            f"    "
            f"{overlap:.6f}"
        )

        print()
        print(
            "Pericynthion:"
        )

        print(
            f"  "
            f"{pericynthion.isoformat()}"
        )

        print(
            "  inside derived occultation: TRUE"
        )

        print(
            "  geometrically occulted: TRUE"
        )

        print()
        print(
            "Products checked:"
        )

        print(
            "  sampled geometry rows: 3262"
        )

        print(
            "  summary: PASS"
        )

        print(
            "  figure: PASS"
        )

        print()
        print(
            "Guardrails:"
        )

        print(
            "  geometric occultation != "
            "actual DSN availability"
        )

        print(
            "  Earth center != "
            "individual DSN antenna"
        )

        print(
            "  RF occultation != "
            "O2O optical availability"
        )

        print()
        print(
            "OK: Phase 2G.1 geocentric lunar "
            "occultation contacts, NASA public "
            "window consistency, pericynthion "
            "containment, sampled geometry, "
            "figure, and interpretation "
            "guardrails independently validated."
        )

    finally:
        spice.kclear()


if __name__ == "__main__":
    main()