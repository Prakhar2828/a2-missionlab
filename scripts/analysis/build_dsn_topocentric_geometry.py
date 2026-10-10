from __future__ import annotations

import csv
import hashlib
import json
import math
from bisect import bisect_right
from datetime import datetime, timedelta, timezone
from pathlib import Path

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

REFERENCE_PATH = (
    ROOT
    / "data"
    / "reference"
    / "dsn_topocentric_geometry_reference.json"
)

COMM_REFERENCE_PATH = (
    ROOT
    / "data"
    / "reference"
    / "artemis_ii_communications_events.json"
)

GEOCENTRIC_SUMMARY_PATH = (
    ROOT
    / "data"
    / "processed"
    / "communications"
    / "lunar_occultation_summary.json"
)

OUTPUT_CSV = (
    ROOT
    / "data"
    / "processed"
    / "communications"
    / "dsn_topocentric_geometry.csv"
)

OUTPUT_SUMMARY = (
    ROOT
    / "data"
    / "processed"
    / "communications"
    / "dsn_topocentric_summary.json"
)

OCCULTATION_FIGURE = (
    ROOT
    / "docs"
    / "assets"
    / "communications"
    / "phase2g2_dsn_topocentric_occultation.svg"
)

ELEVATION_FIGURE = (
    ROOT
    / "docs"
    / "assets"
    / "communications"
    / "phase2g2_dsn_station_elevation.svg"
)

SPICE_DIR = (
    ROOT
    / "data"
    / "raw"
    / "spice"
)

C_KM_S = 299792.458
JULIAN_YEAR_SECONDS = 365.25 * 86400.0

plt.rcParams["svg.hashsalt"] = "a2-missionlab"
SVG_METADATA = {"Date": None}


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
        value.astimezone(
            timezone.utc
        )
        .isoformat(
            timespec="microseconds"
        )
        .replace(
            "+00:00",
            "Z",
        )
    )


def spice_time(value: datetime) -> str:
    return (
        value.astimezone(
            timezone.utc
        ).strftime(
            "%Y-%m-%d %H:%M:%S.%f"
        )
        + " UTC"
    )


def sha256(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as f:
        while True:
            chunk = f.read(
                1024 * 1024
            )

            if not chunk:
                break

            digest.update(chunk)

    return digest.hexdigest().upper()


def dot(a, b) -> float:
    return sum(
        x * y
        for x, y in zip(a, b)
    )


def norm(vector) -> float:
    return math.sqrt(
        dot(vector, vector)
    )


def subtract(a, b):
    return [
        x - y
        for x, y in zip(a, b)
    ]


def scale(vector, factor):
    return [
        factor * value
        for value in vector
    ]


def unit(vector):
    magnitude = norm(vector)

    return [
        value / magnitude
        for value in vector
    ]


def normalize_svg(path: Path) -> None:
    text = path.read_text(
        encoding="utf-8",
    )

    path.write_text(
        "\n".join(
            line.rstrip(" \t")
            for line in text.splitlines()
        )
        + "\n",
        encoding="utf-8",
    )


def load_trajectory():
    if not TRAJECTORY_PATH.exists():
        fail(
            "Missing primary trajectory."
        )

    rows = []

    with TRAJECTORY_PATH.open(
        "r",
        encoding="utf-8-sig",
    ) as f:
        reader = csv.DictReader(f)

        required = {
            "timestamp_utc",
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
                "Primary trajectory missing:\n"
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

                    "position": [
                        float(row["x_km"]),
                        float(row["y_km"]),
                        float(row["z_km"]),
                    ],

                    "velocity": [
                        float(row["vx_km_s"]),
                        float(row["vy_km_s"]),
                        float(row["vz_km_s"]),
                    ],
                }
            )

    rows.sort(
        key=lambda row:
            row["timestamp"]
    )

    if len(rows) != 3262:
        fail(
            "Expected 3262 primary "
            "trajectory states."
        )

    return rows


def hermite_position(
    row0,
    row1,
    timestamp,
):
    dt = (
        row1["timestamp"]
        - row0["timestamp"]
    ).total_seconds()

    if dt <= 0.0:
        fail(
            "Invalid Hermite interval."
        )

    elapsed = (
        timestamp
        - row0["timestamp"]
    ).total_seconds()

    s = max(
        0.0,
        min(
            1.0,
            elapsed / dt,
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
            * row0["position"][i]
            + h10
            * dt
            * row0["velocity"][i]
            + h01
            * row1["position"][i]
            + h11
            * dt
            * row1["velocity"][i]
        )
        for i in range(3)
    ]


class TopocentricModel:
    def __init__(
        self,
        trajectory,
        reference,
        moon_radius_km,
    ):
        self.trajectory = trajectory

        self.times = [
            row["timestamp"]
            for row in trajectory
        ]

        self.moon_radius_km = (
            moon_radius_km
        )

        self.stations = {
            station["station"]:
                station
            for station in reference[
                "reference_stations"
            ]
        }

        earth_reference = (
            reference[
                "earth_reference"
            ]
        )

        self.earth_re_km = (
            float(
                earth_reference[
                    "reference_spheroid_equatorial_radius_m"
                ]
            )
            / 1000.0
        )

        inverse_flattening = float(
            earth_reference[
                "inverse_flattening"
            ]
        )

        self.earth_flattening = (
            1.0
            / inverse_flattening
        )

        self.station_epoch_et = (
            spice.str2et(
                "2003 JAN 01 "
                "00:00:00 TDB"
            )
        )

    def orion_position(
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
                len(self.trajectory) - 2,
                index,
            ),
        )

        return hermite_position(
            self.trajectory[index],
            self.trajectory[index + 1],
            timestamp,
        )

    def moon_position(
        self,
        timestamp,
    ):
        et = spice.str2et(
            spice_time(timestamp)
        )

        state, _ = spice.spkezr(
            "MOON",
            et,
            "J2000",
            "NONE",
            "EARTH",
        )

        return [
            float(state[i])
            for i in range(3)
        ]

    def station_itrf93(
        self,
        station_name,
        timestamp,
    ):
        station = (
            self.stations[
                station_name
            ]
        )

        et = spice.str2et(
            spice_time(timestamp)
        )

        elapsed_years = (
            et - self.station_epoch_et
        ) / JULIAN_YEAR_SECONDS

        position_m = (
            station[
                "position_itrf93_m_at_2003_epoch"
            ]
        )

        velocity = (
            station[
                "velocity_itrf93_m_per_year"
            ]
        )

        return [
            (
                float(position_m[i])
                + elapsed_years
                * float(velocity[i])
            )
            / 1000.0
            for i in range(3)
        ]

    def station_j2000(
        self,
        station_name,
        timestamp,
    ):
        et = spice.str2et(
            spice_time(timestamp)
        )

        station_itrf = (
            self.station_itrf93(
                station_name,
                timestamp,
            )
        )

        transform = spice.pxform(
            "ITRF93",
            "J2000",
            et,
        )

        vector = spice.mxv(
            transform,
            station_itrf,
        )

        return [
            float(value)
            for value in vector
        ]

    def elevation_deg(
        self,
        station_name,
        timestamp,
        orion_j2000,
    ):
        et = spice.str2et(
            spice_time(timestamp)
        )

        station_itrf = (
            self.station_itrf93(
                station_name,
                timestamp,
            )
        )

        transform = spice.pxform(
            "J2000",
            "ITRF93",
            et,
        )

        orion_itrf = spice.mxv(
            transform,
            orion_j2000,
        )

        station_to_orion = subtract(
            orion_itrf,
            station_itrf,
        )

        longitude, latitude, _ = (
            spice.recgeo(
                station_itrf,
                self.earth_re_km,
                self.earth_flattening,
            )
        )

        up = [
            math.cos(latitude)
            * math.cos(longitude),

            math.cos(latitude)
            * math.sin(longitude),

            math.sin(latitude),
        ]

        sine_elevation = dot(
            unit(station_to_orion),
            up,
        )

        sine_elevation = max(
            -1.0,
            min(
                1.0,
                sine_elevation,
            ),
        )

        return math.degrees(
            math.asin(
                sine_elevation
            )
        )

    def geometry(
        self,
        station_name,
        timestamp,
    ):
        orion = (
            self.orion_position(
                timestamp
            )
        )

        moon = (
            self.moon_position(
                timestamp
            )
        )

        station = (
            self.station_j2000(
                station_name,
                timestamp,
            )
        )

        station_to_orion = subtract(
            orion,
            station,
        )

        station_to_moon = subtract(
            moon,
            station,
        )

        denominator = dot(
            station_to_orion,
            station_to_orion,
        )

        projection_fraction = (
            dot(
                station_to_moon,
                station_to_orion,
            )
            / denominator
        )

        projected = scale(
            station_to_orion,
            projection_fraction,
        )

        perpendicular = subtract(
            station_to_moon,
            projected,
        )

        center_distance_km = norm(
            perpendicular
        )

        clearance_km = (
            center_distance_km
            - self.moon_radius_km
        )

        moon_between = (
            0.0
            < projection_fraction
            < 1.0
        )

        occulted = (
            moon_between
            and clearance_km < 0.0
        )

        elevation = (
            self.elevation_deg(
                station_name,
                timestamp,
                orion,
            )
        )

        station_orion_range_km = norm(
            station_to_orion
        )

        return {
            "timestamp":
                timestamp,

            "station":
                station_name,

            "projection_fraction":
                projection_fraction,

            "moon_between":
                moon_between,

            "lunar_limb_clearance_km":
                clearance_km,

            "los_moon_center_distance_km":
                center_distance_km,

            "occulted":
                occulted,

            "orion_elevation_deg":
                elevation,

            "station_orion_range_km":
                station_orion_range_km,

            "one_way_light_time_s":
                (
                    station_orion_range_km
                    / C_KM_S
                ),
        }


def refine_contact(
    model,
    station_name,
    left,
    right,
):
    left_value = (
        model.geometry(
            station_name,
            left,
        )[
            "lunar_limb_clearance_km"
        ]
    )

    right_value = (
        model.geometry(
            station_name,
            right,
        )[
            "lunar_limb_clearance_km"
        ]
    )

    if (
        left_value
        * right_value
        > 0.0
    ):
        fail(
            "Contact root not bracketed "
            f"for {station_name}."
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
                seconds=width / 2.0
            )
        )

        middle_value = (
            model.geometry(
                station_name,
                middle,
            )[
                "lunar_limb_clearance_km"
            ]
        )

        if (
            left_value
            * middle_value
            <= 0.0
        ):
            right = middle
            right_value = (
                middle_value
            )

        else:
            left = middle
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


def build_time_grid(
    start,
    stop,
    step_seconds,
):
    rows = []
    current = start

    while current <= stop:
        rows.append(current)

        current = (
            current
            + timedelta(
                seconds=step_seconds
            )
        )

    return rows


def build_occultation_figure(
    rows,
    nasa_los,
    nasa_aos,
):
    OCCULTATION_FIGURE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fig, ax = plt.subplots(
        figsize=(12, 6.5)
    )

    station_names = sorted(
        {
            row["station"]
            for row in rows
        }
    )

    for station_name in station_names:
        subset = [
            row
            for row in rows
            if row["station"]
            == station_name
        ]

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
            linewidth=1.4,
            label=station_name,
        )

    ax.axhline(
        0.0,
        linestyle="--",
        linewidth=1.0,
        label="Lunar limb",
    )

    ax.axvline(
        nasa_los,
        linestyle=":",
        linewidth=1.2,
        label="NASA LOS",
    )

    ax.axvline(
        nasa_aos,
        linestyle=":",
        linewidth=1.2,
        label="NASA AOS",
    )

    ax.set_title(
        "Artemis II Topocentric DSN "
        "Lunar Occultation Geometry"
    )

    ax.set_xlabel("UTC")

    ax.set_ylabel(
        "Lunar-limb clearance "
        "from station-Orion LOS (km)"
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
        OCCULTATION_FIGURE,
        format="svg",
        metadata=SVG_METADATA,
        bbox_inches="tight",
    )

    plt.close(fig)

    normalize_svg(
        OCCULTATION_FIGURE
    )


def build_elevation_figure(
    rows,
    nasa_los,
    nasa_aos,
):
    ELEVATION_FIGURE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fig, ax = plt.subplots(
        figsize=(12, 6.5)
    )

    station_names = sorted(
        {
            row["station"]
            for row in rows
        }
    )

    for station_name in station_names:
        subset = [
            row
            for row in rows
            if row["station"]
            == station_name
        ]

        ax.plot(
            [
                row["timestamp"]
                for row in subset
            ],
            [
                row[
                    "orion_elevation_deg"
                ]
                for row in subset
            ],
            linewidth=1.4,
            label=station_name,
        )

    ax.axhline(
        0.0,
        linestyle="--",
        linewidth=1.0,
        label="Geometric horizon",
    )

    ax.axvline(
        nasa_los,
        linestyle=":",
        linewidth=1.2,
        label="NASA LOS",
    )

    ax.axvline(
        nasa_aos,
        linestyle=":",
        linewidth=1.2,
        label="NASA AOS",
    )

    ax.set_title(
        "Artemis II Orion Elevation "
        "from DSN Reference Stations"
    )

    ax.set_xlabel("UTC")

    ax.set_ylabel(
        "Geodetic elevation (deg)"
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
        ELEVATION_FIGURE,
        format="svg",
        metadata=SVG_METADATA,
        bbox_inches="tight",
    )

    plt.close(fig)

    normalize_svg(
        ELEVATION_FIGURE
    )


def main() -> None:
    reference = load_json(
        REFERENCE_PATH
    )

    communications_reference = (
        load_json(
            COMM_REFERENCE_PATH
        )
    )

    geocentric_summary = (
        load_json(
            GEOCENTRIC_SUMMARY_PATH
        )
    )

    trajectory = load_trajectory()

    earth_reference = (
        reference[
            "earth_reference"
        ]
    )

    earth_bpc = (
        SPICE_DIR
        / earth_reference[
            "orientation_kernel"
        ]
    )

    expected_hash = (
        earth_reference[
            "orientation_kernel_sha256"
        ]
    )

    if not earth_bpc.exists():
        fail(
            "Missing Earth orientation "
            "binary PCK."
        )

    observed_hash = sha256(
        earth_bpc
    )

    if observed_hash != expected_hash:
        fail(
            "Earth orientation kernel "
            "SHA256 mismatch."
        )

    kernels = [
        SPICE_DIR / "naif0012.tls",
        SPICE_DIR / "de440s.bsp",
        SPICE_DIR / "pck00011.tpc",
        earth_bpc,
    ]

    for kernel in kernels:
        if not kernel.exists():
            fail(
                "Missing required kernel:\n"
                f"{kernel}"
            )

    nasa_window = (
        communications_reference[
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

    geocentric_window = (
        geocentric_summary[
            "geocentric_occultation_window"
        ]
    )

    geocentric_ingress = parse_utc(
        geocentric_window[
            "ingress_utc"
        ]
    )

    geocentric_egress = parse_utc(
        geocentric_window[
            "egress_utc"
        ]
    )

    geocentric_total_offset = (
        abs(
            (
                geocentric_ingress
                - nasa_los
            ).total_seconds()
        )
        + abs(
            (
                geocentric_egress
                - nasa_aos
            ).total_seconds()
        )
    )

    model_reference = (
        reference["model"]
    )

    analysis_start = parse_utc(
        model_reference[
            "analysis_window_start_utc"
        ]
    )

    analysis_stop = parse_utc(
        model_reference[
            "analysis_window_stop_utc"
        ]
    )

    sample_step_seconds = int(
        model_reference[
            "sampling_interval_seconds"
        ]
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

        moon_radius_km = float(
            sum(moon_radii)
            / 3.0
        )

        model = TopocentricModel(
            trajectory,
            reference,
            moon_radius_km,
        )

        timestamps = build_time_grid(
            analysis_start,
            analysis_stop,
            sample_step_seconds,
        )

        sampled_rows = []
        station_results = []

        stations = (
            reference[
                "reference_stations"
            ]
        )

        for station in stations:
            station_name = (
                station["station"]
            )

            station_samples = [
                model.geometry(
                    station_name,
                    timestamp,
                )
                for timestamp in timestamps
            ]

            sampled_rows.extend(
                station_samples
            )

            brackets = []

            for left, right in zip(
                station_samples[:-1],
                station_samples[1:],
            ):
                if not (
                    left["moon_between"]
                    and right["moon_between"]
                ):
                    continue

                if (
                    left[
                        "lunar_limb_clearance_km"
                    ]
                    * right[
                        "lunar_limb_clearance_km"
                    ]
                    < 0.0
                ):
                    brackets.append(
                        (
                            left["timestamp"],
                            right["timestamp"],
                        )
                    )

            if len(brackets) != 2:
                fail(
                    "Expected two contacts for "
                    f"{station_name}, found "
                    f"{len(brackets)}."
                )

            ingress = refine_contact(
                model,
                station_name,
                brackets[0][0],
                brackets[0][1],
            )

            egress = refine_contact(
                model,
                station_name,
                brackets[1][0],
                brackets[1][1],
            )

            ingress_geometry = (
                model.geometry(
                    station_name,
                    ingress,
                )
            )

            egress_geometry = (
                model.geometry(
                    station_name,
                    egress,
                )
            )

            nasa_los_geometry = (
                model.geometry(
                    station_name,
                    nasa_los,
                )
            )

            nasa_aos_geometry = (
                model.geometry(
                    station_name,
                    nasa_aos,
                )
            )

            duration_seconds = (
                egress - ingress
            ).total_seconds()

            ingress_vs_geo = (
                ingress
                - geocentric_ingress
            ).total_seconds()

            egress_vs_geo = (
                egress
                - geocentric_egress
            ).total_seconds()

            ingress_vs_nasa = (
                ingress - nasa_los
            ).total_seconds()

            egress_vs_nasa = (
                egress - nasa_aos
            ).total_seconds()

            total_offset = (
                abs(ingress_vs_nasa)
                + abs(egress_vs_nasa)
            )

            horizon_plausible = (
                nasa_los_geometry[
                    "orion_elevation_deg"
                ] > 0.0
                and nasa_aos_geometry[
                    "orion_elevation_deg"
                ] > 0.0
            )

            station_results.append(
                {
                    "station":
                        station_name,

                    "complex":
                        station["complex"],

                    "diameter_m":
                        station[
                            "diameter_m"
                        ],

                    "operational_assignment_claimed":
                        False,

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

                    "ingress_shift_from_geocentric_seconds":
                        ingress_vs_geo,

                    "egress_shift_from_geocentric_seconds":
                        egress_vs_geo,

                    "ingress_minus_nasa_los_seconds":
                        ingress_vs_nasa,

                    "egress_minus_nasa_aos_seconds":
                        egress_vs_nasa,

                    "total_absolute_nasa_contact_offset_seconds":
                        total_offset,

                    "orion_elevation_deg_at_geometric_ingress":
                        ingress_geometry[
                            "orion_elevation_deg"
                        ],

                    "orion_elevation_deg_at_geometric_egress":
                        egress_geometry[
                            "orion_elevation_deg"
                        ],

                    "orion_elevation_deg_at_nasa_los":
                        nasa_los_geometry[
                            "orion_elevation_deg"
                        ],

                    "orion_elevation_deg_at_nasa_aos":
                        nasa_aos_geometry[
                            "orion_elevation_deg"
                        ],

                    "occulted_at_nasa_los":
                        nasa_los_geometry[
                            "occulted"
                        ],

                    "occulted_at_nasa_aos":
                        nasa_aos_geometry[
                            "occulted"
                        ],

                    "above_horizon_at_both_nasa_contacts":
                        horizon_plausible,
                }
            )

        station_results.sort(
            key=lambda result:
                result[
                    "total_absolute_nasa_contact_offset_seconds"
                ]
        )

        plausible = [
            result["station"]
            for result in station_results
            if result[
                "above_horizon_at_both_nasa_contacts"
            ]
        ]

        best = station_results[0]

        improvement_fraction = (
            (
                geocentric_total_offset
                - best[
                    "total_absolute_nasa_contact_offset_seconds"
                ]
            )
            / geocentric_total_offset
        )

        OUTPUT_CSV.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        fieldnames = [
            "station",
            "timestamp_utc",
            "projection_fraction",
            "moon_between_station_and_orion",
            "lunar_limb_clearance_km",
            "los_moon_center_distance_km",
            "geometrically_occulted",
            "orion_elevation_deg",
            "station_orion_range_km",
            "one_way_light_time_s",
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

            for row in sampled_rows:
                writer.writerow(
                    {
                        "station":
                            row["station"],

                        "timestamp_utc":
                            iso_z(
                                row[
                                    "timestamp"
                                ]
                            ),

                        "projection_fraction":
                            (
                                f"{row['projection_fraction']:.12f}"
                            ),

                        "moon_between_station_and_orion":
                            str(
                                row[
                                    "moon_between"
                                ]
                            ).lower(),

                        "lunar_limb_clearance_km":
                            (
                                f"{row['lunar_limb_clearance_km']:.9f}"
                            ),

                        "los_moon_center_distance_km":
                            (
                                f"{row['los_moon_center_distance_km']:.9f}"
                            ),

                        "geometrically_occulted":
                            str(
                                row[
                                    "occulted"
                                ]
                            ).lower(),

                        "orion_elevation_deg":
                            (
                                f"{row['orion_elevation_deg']:.9f}"
                            ),

                        "station_orion_range_km":
                            (
                                f"{row['station_orion_range_km']:.9f}"
                            ),

                        "one_way_light_time_s":
                            (
                                f"{row['one_way_light_time_s']:.9f}"
                            ),
                    }
                )

        build_occultation_figure(
            sampled_rows,
            nasa_los,
            nasa_aos,
        )

        build_elevation_figure(
            sampled_rows,
            nasa_los,
            nasa_aos,
        )

        summary = {
            "product_id":
                "phase2g2_dsn_topocentric_geometry",

            "mission":
                "Artemis II",

            "provenance":
                (
                    "MISSIONLAB_DERIVED_TOPOCENTRIC_"
                    "GEOMETRY_WITH_NAIF_STATION_"
                    "REFERENCE_AND_NASA_REPORTED_TIMING"
                ),

            "reference_dataset_id":
                reference[
                    "dataset_id"
                ],

            "model": {
                "station_frame":
                    "ITRF93",

                "station_epoch":
                    (
                        "2003 JAN 01 "
                        "00:00:00 TDB"
                    ),

                "plate_motion_applied":
                    True,

                "earth_orientation_kernel":
                    earth_reference[
                        "orientation_kernel"
                    ],

                "earth_orientation_kernel_sha256":
                    observed_hash,

                "orion_interpolation":
                    model_reference[
                        "orion_interpolation"
                    ],

                "moon_ephemeris":
                    model_reference[
                        "moon_ephemeris"
                    ],

                "aberration_correction":
                    model_reference[
                        "aberration_correction"
                    ],

                "sampling_interval_seconds":
                    sample_step_seconds,
            },

            "nasa_reference": {
                "los_utc":
                    iso_z(nasa_los),

                "aos_utc":
                    iso_z(nasa_aos),

                "timing_precision":
                    nasa_window[
                        "time_precision"
                    ],
            },

            "geocentric_reference": {
                "ingress_utc":
                    iso_z(
                        geocentric_ingress
                    ),

                "egress_utc":
                    iso_z(
                        geocentric_egress
                    ),

                "total_absolute_nasa_contact_offset_seconds":
                    geocentric_total_offset,
            },

            "station_results":
                station_results,

            "timing_similarity_ranking": [
                result["station"]
                for result in station_results
            ],

            "reference_stations_above_horizon_at_both_nasa_contacts":
                plausible,

            "best_timing_agreement_reference_station":
                best["station"],

            "best_timing_agreement_improvement_fraction_vs_geocentric":
                improvement_fraction,

            "operational_station_assignment_inferred":
                False,

            "interpretation": (
                "The ranking compares pure geometric "
                "timing only. It does not identify "
                "the DSN antenna operationally assigned "
                "to Artemis II."
            ),

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

                "occultation_figure":
                    str(
                        OCCULTATION_FIGURE.relative_to(
                            ROOT
                        )
                    ),

                "elevation_figure":
                    str(
                        ELEVATION_FIGURE.relative_to(
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
            "Phase 2G.2 Topocentric DSN "
            "Geometry Reconstruction"
        )

        print("=" * 58)

        print()
        print(
            "Reference stations:"
        )

        for result in station_results:
            print()
            print(
                f"  {result['station']} "
                f"({result['complex']})"
            )

            print(
                "    ingress:"
            )

            print(
                "      "
                f"{result['ingress_utc']}"
            )

            print(
                "    egress:"
            )

            print(
                "      "
                f"{result['egress_utc']}"
            )

            print(
                "    duration:"
            )

            print(
                "      "
                f"{result['duration_minutes']:.3f} min"
            )

            print(
                "    NASA contact offsets:"
            )

            print(
                "      ingress "
                f"{result['ingress_minus_nasa_los_seconds']:+.3f} s"
            )

            print(
                "      egress  "
                f"{result['egress_minus_nasa_aos_seconds']:+.3f} s"
            )

            print(
                "    NASA LOS elevation:"
            )

            print(
                "      "
                f"{result['orion_elevation_deg_at_nasa_los']:.3f} deg"
            )

            print(
                "    NASA AOS elevation:"
            )

            print(
                "      "
                f"{result['orion_elevation_deg_at_nasa_aos']:.3f} deg"
            )

            print(
                "    above horizon at "
                "both NASA contacts:"
            )

            print(
                "      "
                f"{result['above_horizon_at_both_nasa_contacts']}"
            )

        print()
        print(
            "Geometric plausibility:"
        )

        print(
            "  reference stations above "
            "horizon at both NASA contacts:"
        )

        print(
            "    "
            + (
                ", ".join(plausible)
                if plausible
                else "NONE"
            )
        )

        print()
        print(
            "Timing similarity:"
        )

        print(
            "  best reference station:"
        )

        print(
            f"    {best['station']}"
        )

        print(
            "  geocentric total absolute "
            "NASA offset:"
        )

        print(
            f"    "
            f"{geocentric_total_offset:.3f} s"
        )

        print(
            "  best topocentric total "
            "absolute NASA offset:"
        )

        print(
            "    "
            f"{best['total_absolute_nasa_contact_offset_seconds']:.3f} s"
        )

        print(
            "  improvement:"
        )

        print(
            "    "
            f"{100.0 * improvement_fraction:.3f}%"
        )

        print()
        print(
            "Operational assignment:"
        )

        print(
            "  inferred: FALSE"
        )

        print()
        print(
            "Wrote:"
        )

        print(
            "  "
            f"{OUTPUT_CSV.relative_to(ROOT)}"
        )

        print(
            "  "
            f"{OUTPUT_SUMMARY.relative_to(ROOT)}"
        )

        print(
            "  "
            f"{OCCULTATION_FIGURE.relative_to(ROOT)}"
        )

        print(
            "  "
            f"{ELEVATION_FIGURE.relative_to(ROOT)}"
        )

    finally:
        spice.kclear()


if __name__ == "__main__":
    main()