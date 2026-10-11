from __future__ import annotations

import csv
import json
import math
from bisect import bisect_right
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import median

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
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

SPICE_DIR = (
    ROOT
    / "data"
    / "raw"
    / "spice"
)

OUTPUT_CSV = (
    ROOT
    / "data"
    / "processed"
    / "communications"
    / "lunar_occultation_geometry.csv"
)

OUTPUT_SUMMARY = (
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

C_KM_S = 299792.458

plt.rcParams["svg.hashsalt"] = "a2-missionlab"

SVG_METADATA = {
    "Date": None,
}


def fail(message: str) -> None:
    raise SystemExit(message)


def load_json(path: Path):
    if not path.exists():
        fail(
            "Missing required file:\n"
            f"{path}"
        )

    with path.open(
        "r",
        encoding="utf-8-sig",
    ) as f:
        return json.load(f)


def parse_utc(value: str) -> datetime:
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


def iso_z(value: datetime) -> str:
    return (
        value.astimezone(timezone.utc)
        .isoformat(timespec="microseconds")
        .replace("+00:00", "Z")
    )


def magnitude(vector) -> float:
    return math.sqrt(
        sum(
            component * component
            for component in vector
        )
    )


def dot(a, b) -> float:
    return sum(
        x * y
        for x, y in zip(a, b)
    )


def subtract(a, b):
    return [
        x - y
        for x, y in zip(a, b)
    ]


def scale(vector, factor: float):
    return [
        factor * component
        for component in vector
    ]


def clamp(
    value: float,
    low: float,
    high: float,
) -> float:
    return max(
        low,
        min(
            high,
            value,
        ),
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


def normalize_svg(
    path: Path,
) -> None:
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


def load_trajectory():
    if not TRAJECTORY_PATH.exists():
        fail(
            "Missing primary trajectory:\n"
            f"{TRAJECTORY_PATH}"
        )

    rows = []

    with TRAJECTORY_PATH.open(
        "r",
        encoding="utf-8-sig",
    ) as f:
        reader = csv.DictReader(f)

        required = {
            "timestamp_utc",
            "met",
            "x_km",
            "y_km",
            "z_km",
            "vx_km_s",
            "vy_km_s",
            "vz_km_s",
        }

        missing = (
            required
            - set(
                reader.fieldnames
                or []
            )
        )

        if missing:
            fail(
                "Primary trajectory is "
                "missing required columns:\n"
                + "\n".join(
                    sorted(missing)
                )
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

                    "timestamp_utc":
                        row[
                            "timestamp_utc"
                        ],

                    "met":
                        row[
                            "met"
                        ],

                    "position_km": [
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

                    "velocity_km_s": [
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

    if len(rows) < 2:
        fail(
            "Primary trajectory contains "
            "fewer than two states."
        )

    return rows


def load_pericynthion_time() -> datetime:
    events = load_json(
        TRAJECTORY_EVENTS_PATH
    )

    matches = [
        event
        for event in events
        if event.get("id")
        == "pericynthion"
    ]

    if len(matches) != 1:
        fail(
            "Expected exactly one "
            "pericynthion event."
        )

    return parse_utc(
        matches[0][
            "timestamp_utc"
        ]
    )


def hermite_position(
    row0,
    row1,
    timestamp: datetime,
):
    t0 = row0["timestamp"]
    t1 = row1["timestamp"]

    dt_seconds = (
        t1 - t0
    ).total_seconds()

    if dt_seconds <= 0.0:
        fail(
            "Non-positive trajectory "
            "interpolation interval."
        )

    elapsed = (
        timestamp - t0
    ).total_seconds()

    s = clamp(
        elapsed / dt_seconds,
        0.0,
        1.0,
    )

    s2 = s * s
    s3 = s2 * s

    h00 = (
        2.0 * s3
        - 3.0 * s2
        + 1.0
    )

    h10 = (
        s3
        - 2.0 * s2
        + s
    )

    h01 = (
        -2.0 * s3
        + 3.0 * s2
    )

    h11 = (
        s3
        - s2
    )

    result = []

    for index in range(3):
        value = (
            h00
            * row0[
                "position_km"
            ][index]
            + h10
            * dt_seconds
            * row0[
                "velocity_km_s"
            ][index]
            + h01
            * row1[
                "position_km"
            ][index]
            + h11
            * dt_seconds
            * row1[
                "velocity_km_s"
            ][index]
        )

        result.append(value)

    return result


class GeometryModel:
    def __init__(
        self,
        trajectory,
        moon_radius_km: float,
    ):
        self.trajectory = trajectory

        self.times = [
            row["timestamp"]
            for row in trajectory
        ]

        self.moon_radius_km = (
            moon_radius_km
        )

    def trajectory_segment(
        self,
        timestamp: datetime,
    ):
        if (
            timestamp < self.times[0]
            or timestamp > self.times[-1]
        ):
            fail(
                "Requested interpolation time "
                "lies outside trajectory."
            )

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
                len(self.trajectory) - 2,
                index,
            ),
        )

        return (
            self.trajectory[index],
            self.trajectory[index + 1],
        )

    def orion_position(
        self,
        timestamp: datetime,
    ):
        row0, row1 = (
            self.trajectory_segment(
                timestamp
            )
        )

        return hermite_position(
            row0,
            row1,
            timestamp,
        )

    def moon_position(
        self,
        timestamp: datetime,
    ):
        et = spice.str2et(
            spice_time_string(
                timestamp
            )
        )

        state, _ = spice.spkezr(
            "MOON",
            et,
            "J2000",
            "NONE",
            "EARTH",
        )

        return [
            float(state[0]),
            float(state[1]),
            float(state[2]),
        ]

    def geometry(
        self,
        timestamp: datetime,
        orion_position=None,
    ):
        if orion_position is None:
            orion_position = (
                self.orion_position(
                    timestamp
                )
            )

        moon_position = (
            self.moon_position(
                timestamp
            )
        )

        orion_range_km = (
            magnitude(
                orion_position
            )
        )

        moon_range_km = (
            magnitude(
                moon_position
            )
        )

        orion_norm_sq = dot(
            orion_position,
            orion_position,
        )

        projection_fraction = (
            dot(
                moon_position,
                orion_position,
            )
            / orion_norm_sq
        )

        projected_point = scale(
            orion_position,
            projection_fraction,
        )

        perpendicular_vector = subtract(
            moon_position,
            projected_point,
        )

        los_moon_center_distance_km = (
            magnitude(
                perpendicular_vector
            )
        )

        limb_clearance_km = (
            los_moon_center_distance_km
            - self.moon_radius_km
        )

        moon_between = (
            0.0
            < projection_fraction
            < 1.0
        )

        occulted = (
            moon_between
            and limb_clearance_km
            < 0.0
        )

        cosine_angle = (
            dot(
                moon_position,
                orion_position,
            )
            / (
                moon_range_km
                * orion_range_km
            )
        )

        cosine_angle = clamp(
            cosine_angle,
            -1.0,
            1.0,
        )

        earth_center_angle_deg = (
            math.degrees(
                math.acos(
                    cosine_angle
                )
            )
        )

        return {
            "timestamp":
                timestamp,

            "orion_position_km":
                orion_position,

            "moon_position_km":
                moon_position,

            "orion_range_km":
                orion_range_km,

            "moon_range_km":
                moon_range_km,

            "one_way_light_time_s":
                (
                    orion_range_km
                    / C_KM_S
                ),

            "projection_fraction":
                projection_fraction,

            "moon_between":
                moon_between,

            "los_moon_center_distance_km":
                los_moon_center_distance_km,

            "lunar_limb_clearance_km":
                limb_clearance_km,

            "earth_center_moon_orion_angle_deg":
                earth_center_angle_deg,

            "occulted":
                occulted,
        }


def refine_contact(
    model: GeometryModel,
    left_time: datetime,
    right_time: datetime,
) -> datetime:
    left_value = (
        model.geometry(
            left_time
        )[
            "lunar_limb_clearance_km"
        ]
    )

    right_value = (
        model.geometry(
            right_time
        )[
            "lunar_limb_clearance_km"
        ]
    )

    if left_value == 0.0:
        return left_time

    if right_value == 0.0:
        return right_time

    if (
        left_value
        * right_value
        > 0.0
    ):
        fail(
            "Contact refinement bracket "
            "does not contain a sign change."
        )

    left = left_time
    right = right_time

    for _ in range(80):
        span_seconds = (
            right - left
        ).total_seconds()

        if span_seconds < 1e-6:
            break

        midpoint = (
            left
            + timedelta(
                seconds=(
                    span_seconds / 2.0
                )
            )
        )

        middle_value = (
            model.geometry(
                midpoint
            )[
                "lunar_limb_clearance_km"
            ]
        )

        if middle_value == 0.0:
            return midpoint

        if (
            left_value
            * middle_value
            <= 0.0
        ):
            right = midpoint
            right_value = (
                middle_value
            )

        else:
            left = midpoint
            left_value = (
                middle_value
            )

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


def golden_minimum(
    model: GeometryModel,
    start: datetime,
    stop: datetime,
):
    duration = (
        stop - start
    ).total_seconds()

    phi = (
        math.sqrt(5.0)
        - 1.0
    ) / 2.0

    a = 0.0
    b = duration

    c = (
        b
        - phi
        * (
            b - a
        )
    )

    d = (
        a
        + phi
        * (
            b - a
        )
    )

    def evaluate(
        seconds: float,
    ) -> float:
        timestamp = (
            start
            + timedelta(
                seconds=seconds
            )
        )

        return (
            model.geometry(
                timestamp
            )[
                "lunar_limb_clearance_km"
            ]
        )

    fc = evaluate(c)
    fd = evaluate(d)

    for _ in range(100):
        if (
            b - a
        ) < 1e-5:
            break

        if fc < fd:
            b = d
            d = c
            fd = fc

            c = (
                b
                - phi
                * (
                    b - a
                )
            )

            fc = evaluate(c)

        else:
            a = c
            c = d
            fc = fd

            d = (
                a
                + phi
                * (
                    b - a
                )
            )

            fd = evaluate(d)

    best_seconds = (
        a + b
    ) / 2.0

    best_time = (
        start
        + timedelta(
            seconds=best_seconds
        )
    )

    return model.geometry(
        best_time
    )


def overlap_fraction(
    start_a,
    stop_a,
    start_b,
    stop_b,
) -> float:
    intersection_start = max(
        start_a,
        start_b,
    )

    intersection_stop = min(
        stop_a,
        stop_b,
    )

    intersection = max(
        0.0,
        (
            intersection_stop
            - intersection_start
        ).total_seconds(),
    )

    union_start = min(
        start_a,
        start_b,
    )

    union_stop = max(
        stop_a,
        stop_b,
    )

    union = (
        union_stop
        - union_start
    ).total_seconds()

    if union <= 0.0:
        return 0.0

    return (
        intersection / union
    )


def build_figure(
    sampled_geometry,
    ingress,
    egress,
    nasa_los,
    nasa_aos,
):
    FIGURE_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    plot_start = (
        min(
            ingress,
            nasa_los,
        )
        - timedelta(
            minutes=30
        )
    )

    plot_stop = (
        max(
            egress,
            nasa_aos,
        )
        + timedelta(
            minutes=30
        )
    )

    subset = [
        row
        for row in sampled_geometry
        if (
            plot_start
            <= row["timestamp"]
            <= plot_stop
        )
    ]

    fig, ax = plt.subplots(
        figsize=(
            12,
            6.5,
        )
    )

    ax.plot(
        [
            row["timestamp"]
            for row in subset
        ],
        [
            row[
                "lunar_limb_clearance_km"
            ]
            for row in subset
        ],
        marker="o",
        linewidth=1.3,
        markersize=3.5,
        label=(
            "Sampled Earth-center "
            "lunar-limb clearance"
        ),
    )

    ax.axhline(
        0.0,
        linewidth=1.1,
        linestyle="-",
        label="Geometric lunar limb",
    )

    ax.axvline(
        ingress,
        linewidth=1.2,
        linestyle="--",
        label=(
            "MissionLab geometric "
            "ingress"
        ),
    )

    ax.axvline(
        egress,
        linewidth=1.2,
        linestyle="--",
        label=(
            "MissionLab geometric "
            "egress"
        ),
    )

    ax.axvline(
        nasa_los,
        linewidth=1.1,
        linestyle=":",
        label="NASA public LOS",
    )

    ax.axvline(
        nasa_aos,
        linewidth=1.1,
        linestyle=":",
        label="NASA public AOS",
    )

    ax.set_title(
        "Artemis II Geocentric "
        "Lunar Occultation Geometry"
    )

    ax.set_xlabel(
        "UTC"
    )

    ax.set_ylabel(
        "Moon-limb clearance from "
        "Earth-Orion line of sight (km)"
    )

    ax.grid(
        True,
        alpha=0.25,
    )

    ax.xaxis.set_major_formatter(
        mdates.DateFormatter(
            "%H:%M",
            tz=timezone.utc,
        )
    )

    ax.legend(
        fontsize=8,
        loc="best",
    )

    fig.autofmt_xdate()
    fig.tight_layout()

    fig.savefig(
        FIGURE_PATH,
        format="svg",
        metadata=SVG_METADATA,
        bbox_inches="tight",
    )

    plt.close(fig)

    normalize_svg(
        FIGURE_PATH
    )


def main() -> None:
    reference = load_json(
        REFERENCE_PATH
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

    for kernel in kernels:
        if not kernel.exists():
            fail(
                "Missing required SPICE "
                "kernel:\n"
                f"{kernel}"
            )

    try:
        for kernel in kernels:
            spice.furnsh(
                str(kernel)
            )

        _, moon_radii = spice.bodvrd(
            "MOON",
            "RADII",
            3,
        )

        moon_mean_radius_km = float(
            sum(moon_radii)
            / 3.0
        )

        model = GeometryModel(
            trajectory,
            moon_mean_radius_km,
        )

        sampled_geometry = []

        for row in trajectory:
            geometry = (
                model.geometry(
                    row[
                        "timestamp"
                    ],
                    orion_position=(
                        row[
                            "position_km"
                        ]
                    ),
                )
            )

            geometry[
                "met"
            ] = row[
                "met"
            ]

            sampled_geometry.append(
                geometry
            )

        crossing_brackets = []

        for left, right in zip(
            sampled_geometry[:-1],
            sampled_geometry[1:],
        ):
            if not (
                left["moon_between"]
                and right["moon_between"]
            ):
                continue

            left_value = (
                left[
                    "lunar_limb_clearance_km"
                ]
            )

            right_value = (
                right[
                    "lunar_limb_clearance_km"
                ]
            )

            if (
                left_value
                * right_value
                < 0.0
            ):
                crossing_brackets.append(
                    (
                        left,
                        right,
                    )
                )

        if len(
            crossing_brackets
        ) != 2:
            fail(
                "Expected exactly two "
                "lunar-limb crossing brackets, "
                "found "
                f"{len(crossing_brackets)}."
            )

        contacts = []

        for left, right in (
            crossing_brackets
        ):
            contact_time = refine_contact(
                model,
                left["timestamp"],
                right["timestamp"],
            )

            before_time = (
                contact_time
                - timedelta(
                    seconds=1.0
                )
            )

            after_time = (
                contact_time
                + timedelta(
                    seconds=1.0
                )
            )

            before = (
                model.geometry(
                    before_time
                )
            )

            after = (
                model.geometry(
                    after_time
                )
            )

            if (
                not before["occulted"]
                and after["occulted"]
            ):
                contact_type = (
                    "INGRESS_LOS"
                )

            elif (
                before["occulted"]
                and not after["occulted"]
            ):
                contact_type = (
                    "EGRESS_AOS"
                )

            else:
                fail(
                    "Could not classify "
                    "refined lunar-limb contact."
                )

            geometry = (
                model.geometry(
                    contact_time
                )
            )

            contacts.append(
                {
                    "contact_type":
                        contact_type,

                    "timestamp":
                        contact_time,

                    "geometry":
                        geometry,
                }
            )

        contacts.sort(
            key=lambda item:
                item["timestamp"]
        )

        ingress = (
            contacts[0][
                "timestamp"
            ]
        )

        egress = (
            contacts[1][
                "timestamp"
            ]
        )

        if (
            contacts[0][
                "contact_type"
            ]
            != "INGRESS_LOS"
        ):
            fail(
                "First refined contact "
                "is not ingress."
            )

        if (
            contacts[1][
                "contact_type"
            ]
            != "EGRESS_AOS"
        ):
            fail(
                "Second refined contact "
                "is not egress."
            )

        duration_seconds = (
            egress - ingress
        ).total_seconds()

        deepest = golden_minimum(
            model,
            ingress,
            egress,
        )

        pericynthion_time = (
            load_pericynthion_time()
        )

        pericynthion_geometry = (
            model.geometry(
                pericynthion_time
            )
        )

        nasa_window = (
            reference[
                "public_lunar_occultation_window"
            ]
        )

        nasa_los = parse_utc(
            nasa_window[
                "loss_of_signal_utc"
            ]
        )

        nasa_aos = parse_utc(
            nasa_window[
                "acquisition_of_signal_utc"
            ]
        )

        nasa_duration_seconds = (
            nasa_aos - nasa_los
        ).total_seconds()

        ingress_offset_seconds = (
            ingress - nasa_los
        ).total_seconds()

        egress_offset_seconds = (
            egress - nasa_aos
        ).total_seconds()

        duration_difference_seconds = (
            duration_seconds
            - nasa_duration_seconds
        )

        window_overlap_fraction = (
            overlap_fraction(
                ingress,
                egress,
                nasa_los,
                nasa_aos,
            )
        )

        cadences = [
            (
                trajectory[index][
                    "timestamp"
                ]
                - trajectory[
                    index - 1
                ][
                    "timestamp"
                ]
            ).total_seconds()
            for index in range(
                1,
                len(trajectory),
            )
        ]

        OUTPUT_CSV.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        fieldnames = [
            "timestamp_utc",
            "met",
            "orion_range_km",
            "moon_range_km",
            "one_way_light_time_s",
            "projection_fraction",
            "moon_between_earth_and_orion",
            "los_moon_center_distance_km",
            "lunar_limb_clearance_km",
            "earth_center_moon_orion_angle_deg",
            "geometrically_occulted",
        ]

        with OUTPUT_CSV.open(
            "w",
            newline="",
            encoding="utf-8",
        ) as f:
            writer = csv.DictWriter(
                f,
                fieldnames=fieldnames,
            )

            writer.writeheader()

            for row in sampled_geometry:
                writer.writerow(
                    {
                        "timestamp_utc":
                            iso_z(
                                row[
                                    "timestamp"
                                ]
                            ),

                        "met":
                            row["met"],

                        "orion_range_km":
                            (
                                f"{row['orion_range_km']:.9f}"
                            ),

                        "moon_range_km":
                            (
                                f"{row['moon_range_km']:.9f}"
                            ),

                        "one_way_light_time_s":
                            (
                                f"{row['one_way_light_time_s']:.9f}"
                            ),

                        "projection_fraction":
                            (
                                f"{row['projection_fraction']:.12f}"
                            ),

                        "moon_between_earth_and_orion":
                            str(
                                row[
                                    "moon_between"
                                ]
                            ).lower(),

                        "los_moon_center_distance_km":
                            (
                                f"{row['los_moon_center_distance_km']:.9f}"
                            ),

                        "lunar_limb_clearance_km":
                            (
                                f"{row['lunar_limb_clearance_km']:.9f}"
                            ),

                        "earth_center_moon_orion_angle_deg":
                            (
                                f"{row['earth_center_moon_orion_angle_deg']:.12f}"
                            ),

                        "geometrically_occulted":
                            str(
                                row[
                                    "occulted"
                                ]
                            ).lower(),
                    }
                )

        build_figure(
            sampled_geometry,
            ingress,
            egress,
            nasa_los,
            nasa_aos,
        )

        summary = {
            "product_id":
                "phase2g1_geocentric_lunar_occultation",

            "mission":
                "Artemis II",

            "provenance":
                (
                    "MISSIONLAB_DERIVED_GEOMETRY_"
                    "WITH_NASA_REPORTED_VALIDATION_REFERENCE"
                ),

            "reference_dataset_id":
                reference[
                    "dataset_id"
                ],

            "model": {
                "observer":
                    "EARTH_CENTER",

                "target":
                    "ORION",

                "occulter":
                    "MOON",

                "coordinate_frame":
                    "J2000",

                "moon_shape":
                    (
                        "SPHERE_USING_SPICE_"
                        "MEAN_RADIUS"
                    ),

                "moon_mean_radius_km":
                    moon_mean_radius_km,

                "moon_ephemeris":
                    "SPICE_DE440S",

                "aberration_correction":
                    "NONE",

                "orion_interpolation":
                    (
                        "PIECEWISE_CUBIC_HERMITE_"
                        "POSITION_USING_PUBLIC_OEM_"
                        "POSITION_AND_VELOCITY"
                    ),
            },

            "trajectory": {
                "sample_count":
                    len(trajectory),

                "start_utc":
                    iso_z(
                        trajectory[
                            0
                        ][
                            "timestamp"
                        ]
                    ),

                "stop_utc":
                    iso_z(
                        trajectory[
                            -1
                        ][
                            "timestamp"
                        ]
                    ),

                "cadence_seconds": {
                    "minimum":
                        min(cadences),

                    "median":
                        median(cadences),

                    "maximum":
                        max(cadences),
                },
            },

            "refined_contacts": [
                {
                    "contact_type":
                        contact[
                            "contact_type"
                        ],

                    "timestamp_utc":
                        iso_z(
                            contact[
                                "timestamp"
                            ]
                        ),

                    "lunar_limb_clearance_km":
                        contact[
                            "geometry"
                        ][
                            "lunar_limb_clearance_km"
                        ],

                    "projection_fraction":
                        contact[
                            "geometry"
                        ][
                            "projection_fraction"
                        ],
                }
                for contact in contacts
            ],

            "geocentric_occultation_window": {
                "ingress_utc":
                    iso_z(ingress),

                "egress_utc":
                    iso_z(egress),

                "duration_seconds":
                    duration_seconds,

                "duration_minutes":
                    (
                        duration_seconds
                        / 60.0
                    ),
            },

            "deepest_geometric_occultation": {
                "timestamp_utc":
                    iso_z(
                        deepest[
                            "timestamp"
                        ]
                    ),

                "lunar_limb_clearance_km":
                    deepest[
                        "lunar_limb_clearance_km"
                    ],

                "los_moon_center_distance_km":
                    deepest[
                        "los_moon_center_distance_km"
                    ],

                "earth_orion_range_km":
                    deepest[
                        "orion_range_km"
                    ],

                "one_way_light_time_s":
                    deepest[
                        "one_way_light_time_s"
                    ],
            },

            "pericynthion_context": {
                "timestamp_utc":
                    iso_z(
                        pericynthion_time
                    ),

                "inside_geocentric_occultation":
                    (
                        ingress
                        < pericynthion_time
                        < egress
                    ),

                "geometrically_occulted":
                    pericynthion_geometry[
                        "occulted"
                    ],

                "lunar_limb_clearance_km":
                    pericynthion_geometry[
                        "lunar_limb_clearance_km"
                    ],

                "earth_orion_range_km":
                    pericynthion_geometry[
                        "orion_range_km"
                    ],

                "one_way_light_time_s":
                    pericynthion_geometry[
                        "one_way_light_time_s"
                    ],
            },

            "nasa_public_reference": {
                "loss_of_signal_utc":
                    iso_z(nasa_los),

                "acquisition_of_signal_utc":
                    iso_z(nasa_aos),

                "duration_seconds":
                    nasa_duration_seconds,

                "time_precision":
                    nasa_window[
                        "time_precision"
                    ],
            },

            "nasa_comparison": {
                "ingress_minus_nasa_los_seconds":
                    ingress_offset_seconds,

                "egress_minus_nasa_aos_seconds":
                    egress_offset_seconds,

                "duration_difference_seconds":
                    duration_difference_seconds,

                "window_overlap_fraction":
                    window_overlap_fraction,

                "interpretation":
                    (
                        "Offsets are expected because "
                        "the MissionLab model uses the "
                        "Earth center while NASA's "
                        "communications window represents "
                        "operational Earth-based network "
                        "contact timing."
                    ),
            },

            "guardrails":
                reference[
                    "guardrails"
                ],

            "outputs": {
                "sampled_geometry_csv":
                    str(
                        OUTPUT_CSV.relative_to(
                            ROOT
                        )
                    ),

                "figure":
                    str(
                        FIGURE_PATH.relative_to(
                            ROOT
                        )
                    ),
            },
        }

        OUTPUT_SUMMARY.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with OUTPUT_SUMMARY.open(
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(
                summary,
                f,
                indent=2,
            )

        print()
        print(
            "Phase 2G.1 Geocentric Lunar "
            "Occultation Reconstruction"
        )

        print(
            "=" * 59
        )

        print()
        print(
            "Model:"
        )

        print(
            "  observer: Earth center"
        )

        print(
            "  target: Orion"
        )

        print(
            "  occulter: spherical Moon"
        )

        print(
            "  frame: J2000"
        )

        print(
            "  Orion interpolation: "
            "piecewise cubic Hermite"
        )

        print(
            "  Moon ephemeris: "
            "SPICE DE440S"
        )

        print(
            "  aberration correction: NONE"
        )

        print(
            "  Moon mean radius:"
        )

        print(
            f"    "
            f"{moon_mean_radius_km:.6f} km"
        )

        print()
        print(
            "Trajectory:"
        )

        print(
            f"  samples: "
            f"{len(trajectory)}"
        )

        print(
            f"  median cadence: "
            f"{median(cadences):.3f} s"
        )

        print()
        print(
            "Refined geometric contacts:"
        )

        print(
            "  ingress / LOS:"
        )

        print(
            f"    {iso_z(ingress)}"
        )

        print(
            "  egress / AOS:"
        )

        print(
            f"    {iso_z(egress)}"
        )

        print(
            "  duration:"
        )

        print(
            f"    "
            f"{duration_seconds:.3f} s"
        )

        print(
            f"    "
            f"{duration_seconds / 60.0:.3f} min"
        )

        print()
        print(
            "NASA public reference:"
        )

        print(
            "  LOS:"
        )

        print(
            f"    {iso_z(nasa_los)}"
        )

        print(
            "  AOS:"
        )

        print(
            f"    {iso_z(nasa_aos)}"
        )

        print(
            "  duration:"
        )

        print(
            f"    "
            f"{nasa_duration_seconds:.3f} s"
        )

        print()
        print(
            "Comparison:"
        )

        print(
            "  ingress - NASA LOS:"
        )

        print(
            f"    "
            f"{ingress_offset_seconds:+.3f} s"
        )

        print(
            "  egress - NASA AOS:"
        )

        print(
            f"    "
            f"{egress_offset_seconds:+.3f} s"
        )

        print(
            "  duration difference:"
        )

        print(
            f"    "
            f"{duration_difference_seconds:+.3f} s"
        )

        print(
            "  window overlap fraction:"
        )

        print(
            f"    "
            f"{window_overlap_fraction:.6f}"
        )

        print()
        print(
            "Deepest geometric occultation:"
        )

        print(
            "  UTC:"
        )

        print(
            f"    "
            f"{iso_z(deepest['timestamp'])}"
        )

        print(
            "  lunar-limb clearance:"
        )

        print(
            f"    "
            f"{deepest['lunar_limb_clearance_km']:.3f} km"
        )

        print(
            "  Earth-Orion range:"
        )

        print(
            f"    "
            f"{deepest['orion_range_km']:,.3f} km"
        )

        print(
            "  one-way light time:"
        )

        print(
            f"    "
            f"{deepest['one_way_light_time_s']:.6f} s"
        )

        print()
        print(
            "Pericynthion:"
        )

        print(
            f"  UTC: "
            f"{iso_z(pericynthion_time)}"
        )

        print(
            "  inside occultation:"
        )

        print(
            "    "
            f"{ingress < pericynthion_time < egress}"
        )

        print(
            "  geometrically occulted:"
        )

        print(
            "    "
            f"{pericynthion_geometry['occulted']}"
        )

        print()
        print(
            "Interpretation boundary:"
        )

        print(
            "  geometric occultation != "
            "actual DSN link availability"
        )

        print(
            "  Earth-center geometry != "
            "individual DSN antenna geometry"
        )

        print(
            "  RF occultation != "
            "O2O optical availability"
        )

        print()
        print(
            "Wrote:"
        )

        print(
            f"  "
            f"{OUTPUT_CSV.relative_to(ROOT)}"
        )

        print(
            f"  "
            f"{OUTPUT_SUMMARY.relative_to(ROOT)}"
        )

        print(
            f"  "
            f"{FIGURE_PATH.relative_to(ROOT)}"
        )

    finally:
        spice.kclear()


if __name__ == "__main__":
    main()