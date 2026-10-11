from __future__ import annotations

import csv
import hashlib
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

SUMMARY_PATH = (
    ROOT
    / "data"
    / "processed"
    / "communications"
    / "dsn_topocentric_summary.json"
)

OUTPUT_CSV = (
    ROOT
    / "data"
    / "processed"
    / "communications"
    / "dsn_topocentric_geometry.csv"
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

JULIAN_YEAR_SECONDS = (
    365.25 * 86400.0
)

EXPECTED_REFERENCE_ID = (
    "phase2g2_dsn_topocentric_geometry_reference"
)

EXPECTED_PRODUCT_ID = (
    "phase2g2_dsn_topocentric_geometry"
)

EXPECTED_STATIONS = {
    "DSS-14": {
        "complex": "Goldstone",
        "position": [
            -2353621.420,
            -4641341.472,
            3677052.318,
        ],
        "velocity": [
            -0.0180,
            0.0065,
            -0.0038,
        ],
    },
    "DSS-43": {
        "complex": "Canberra",
        "position": [
            -4460894.917,
            2682361.507,
            -3674748.152,
        ],
        "velocity": [
            -0.0335,
            -0.0041,
            0.0392,
        ],
    },
    "DSS-63": {
        "complex": "Madrid",
        "position": [
            4849092.518,
            -360180.3480,
            4115109.251,
        ],
        "velocity": [
            -0.0100,
            0.0242,
            0.0156,
        ],
    },
}


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


def spice_time(value):
    return (
        value.astimezone(
            timezone.utc
        ).strftime(
            "%Y-%m-%d %H:%M:%S.%f"
        )
        + " UTC"
    )


def sha256(path):
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


def dot(a, b):
    return sum(
        x * y
        for x, y in zip(a, b)
    )


def norm(vector):
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


def load_trajectory():
    rows = []

    with TRAJECTORY_PATH.open(
        "r",
        encoding="utf-8-sig",
    ) as f:
        reader = csv.DictReader(f)

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
            "expected 3262 trajectory states"
        )

    return rows


def hermite(row0, row1, timestamp):
    dt = (
        row1["timestamp"]
        - row0["timestamp"]
    ).total_seconds()

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
        2 * s**3
        - 3 * s**2
        + 1
    )

    h10 = (
        s**3
        - 2 * s**2
        + s
    )

    h01 = (
        -2 * s**3
        + 3 * s**2
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


class IndependentModel:
    def __init__(
        self,
        trajectory,
        stations,
        moon_radius,
        earth_re,
        flattening,
    ):
        self.trajectory = trajectory

        self.times = [
            row["timestamp"]
            for row in trajectory
        ]

        self.stations = stations
        self.moon_radius = moon_radius
        self.earth_re = earth_re
        self.flattening = flattening

        self.epoch_et = spice.str2et(
            "2003 JAN 01 00:00:00 TDB"
        )

    def orion(self, timestamp):
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

        return hermite(
            self.trajectory[index],
            self.trajectory[index + 1],
            timestamp,
        )

    def station_itrf(
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

        years = (
            et - self.epoch_et
        ) / JULIAN_YEAR_SECONDS

        return [
            (
                station["position"][i]
                + years
                * station["velocity"][i]
            )
            / 1000.0
            for i in range(3)
        ]

    def geometry(
        self,
        station_name,
        timestamp,
    ):
        et = spice.str2et(
            spice_time(timestamp)
        )

        orion = self.orion(
            timestamp
        )

        moon_state, _ = spice.spkezr(
            "MOON",
            et,
            "J2000",
            "NONE",
            "EARTH",
        )

        moon = [
            float(moon_state[i])
            for i in range(3)
        ]

        station_itrf = (
            self.station_itrf(
                station_name,
                timestamp,
            )
        )

        to_j2000 = spice.pxform(
            "ITRF93",
            "J2000",
            et,
        )

        station = [
            float(value)
            for value in spice.mxv(
                to_j2000,
                station_itrf,
            )
        ]

        station_to_orion = subtract(
            orion,
            station,
        )

        station_to_moon = subtract(
            moon,
            station,
        )

        projection = (
            dot(
                station_to_moon,
                station_to_orion,
            )
            / dot(
                station_to_orion,
                station_to_orion,
            )
        )

        projected = scale(
            station_to_orion,
            projection,
        )

        perpendicular = subtract(
            station_to_moon,
            projected,
        )

        clearance = (
            norm(perpendicular)
            - self.moon_radius
        )

        moon_between = (
            0 < projection < 1
        )

        to_itrf = spice.pxform(
            "J2000",
            "ITRF93",
            et,
        )

        orion_itrf = spice.mxv(
            to_itrf,
            orion,
        )

        station_to_orion_itrf = (
            subtract(
                orion_itrf,
                station_itrf,
            )
        )

        lon, lat, _ = spice.recgeo(
            station_itrf,
            self.earth_re,
            self.flattening,
        )

        up = [
            math.cos(lat)
            * math.cos(lon),

            math.cos(lat)
            * math.sin(lon),

            math.sin(lat),
        ]

        sine_elevation = dot(
            unit(
                station_to_orion_itrf
            ),
            up,
        )

        sine_elevation = max(
            -1.0,
            min(
                1.0,
                sine_elevation,
            ),
        )

        return {
            "clearance":
                clearance,

            "moon_between":
                moon_between,

            "occulted":
                (
                    moon_between
                    and clearance < 0
                ),

            "elevation":
                math.degrees(
                    math.asin(
                        sine_elevation
                    )
                ),
        }


def refine_root(
    model,
    station,
    left,
    right,
):
    fl = model.geometry(
        station,
        left,
    )["clearance"]

    fr = model.geometry(
        station,
        right,
    )["clearance"]

    if fl * fr > 0:
        fail(
            "contact root is not bracketed"
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
                seconds=width / 2
            )
        )

        fm = model.geometry(
            station,
            middle,
        )["clearance"]

        if fl * fm <= 0:
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
                / 2
            )
        )
    )


def main() -> None:
    reference = load_json(
        REFERENCE_PATH
    )

    communications = load_json(
        COMM_REFERENCE_PATH
    )

    geocentric = load_json(
        GEOCENTRIC_SUMMARY_PATH
    )

    summary = load_json(
        SUMMARY_PATH
    )

    if (
        reference["dataset_id"]
        != EXPECTED_REFERENCE_ID
    ):
        fail(
            "reference dataset ID mismatch"
        )

    if (
        summary["product_id"]
        != EXPECTED_PRODUCT_ID
    ):
        fail(
            "summary product ID mismatch"
        )

    stations = (
        reference[
            "reference_stations"
        ]
    )

    if len(stations) != 3:
        fail(
            "expected three reference stations"
        )

    stations_by_name = {}

    for station in stations:
        name = station["station"]

        if name not in EXPECTED_STATIONS:
            fail(
                f"unexpected station {name}"
            )

        expected = (
            EXPECTED_STATIONS[name]
        )

        if (
            station["complex"]
            != expected["complex"]
        ):
            fail(
                f"{name} complex mismatch"
            )

        observed_position = (
            station[
                "position_itrf93_m_at_2003_epoch"
            ]
        )

        observed_velocity = (
            station[
                "velocity_itrf93_m_per_year"
            ]
        )

        for observed, expected_value in zip(
            observed_position,
            expected["position"],
        ):
            if abs(
                float(observed)
                - expected_value
            ) > 1e-6:
                fail(
                    f"{name} position changed"
                )

        for observed, expected_value in zip(
            observed_velocity,
            expected["velocity"],
        ):
            if abs(
                float(observed)
                - expected_value
            ) > 1e-9:
                fail(
                    f"{name} velocity changed"
                )

        stations_by_name[name] = {
            "position":
                [
                    float(value)
                    for value
                    in observed_position
                ],

            "velocity":
                [
                    float(value)
                    for value
                    in observed_velocity
                ],
        }

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

    if sha256(
        earth_bpc
    ) != earth_reference[
        "orientation_kernel_sha256"
    ]:
        fail(
            "Earth orientation kernel "
            "hash mismatch"
        )

    nasa_window = (
        communications[
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

    geo_window = (
        geocentric[
            "geocentric_occultation_window"
        ]
    )

    geo_ingress = parse_utc(
        geo_window["ingress_utc"]
    )

    geo_egress = parse_utc(
        geo_window["egress_utc"]
    )

    geocentric_total_offset = (
        abs(
            (
                geo_ingress
                - nasa_los
            ).total_seconds()
        )
        + abs(
            (
                geo_egress
                - nasa_aos
            ).total_seconds()
        )
    )

    trajectory = load_trajectory()

    kernels = [
        SPICE_DIR / "naif0012.tls",
        SPICE_DIR / "de440s.bsp",
        SPICE_DIR / "pck00011.tpc",
        earth_bpc,
    ]

    try:
        for kernel in kernels:
            if not kernel.exists():
                fail(
                    f"missing kernel {kernel}"
                )

            spice.furnsh(
                str(kernel)
            )

        _, lunar_radii = spice.bodvrd(
            "MOON",
            "RADII",
            3,
        )

        moon_radius = float(
            sum(lunar_radii)
            / 3
        )

        earth_re = (
            float(
                earth_reference[
                    "reference_spheroid_equatorial_radius_m"
                ]
            )
            / 1000.0
        )

        flattening = (
            1.0
            / float(
                earth_reference[
                    "inverse_flattening"
                ]
            )
        )

        model = IndependentModel(
            trajectory,
            stations_by_name,
            moon_radius,
            earth_re,
            flattening,
        )

        start = parse_utc(
            reference[
                "model"
            ][
                "analysis_window_start_utc"
            ]
        )

        stop = parse_utc(
            reference[
                "model"
            ][
                "analysis_window_stop_utc"
            ]
        )

        step = int(
            reference[
                "model"
            ][
                "sampling_interval_seconds"
            ]
        )

        timestamps = []
        current = start

        while current <= stop:
            timestamps.append(current)

            current += timedelta(
                seconds=step
            )

        independent_results = []

        for station_name in sorted(
            stations_by_name
        ):
            samples = [
                {
                    "timestamp":
                        timestamp,

                    **model.geometry(
                        station_name,
                        timestamp,
                    ),
                }
                for timestamp in timestamps
            ]

            brackets = []

            for left, right in zip(
                samples[:-1],
                samples[1:],
            ):
                if (
                    left["moon_between"]
                    and right["moon_between"]
                    and (
                        left["clearance"]
                        * right["clearance"]
                        < 0
                    )
                ):
                    brackets.append(
                        (
                            left["timestamp"],
                            right["timestamp"],
                        )
                    )

            if len(brackets) != 2:
                fail(
                    f"{station_name} does not "
                    "have two contacts"
                )

            ingress = refine_root(
                model,
                station_name,
                brackets[0][0],
                brackets[0][1],
            )

            egress = refine_root(
                model,
                station_name,
                brackets[1][0],
                brackets[1][1],
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

            ingress_offset = (
                ingress - nasa_los
            ).total_seconds()

            egress_offset = (
                egress - nasa_aos
            ).total_seconds()

            total_offset = (
                abs(ingress_offset)
                + abs(egress_offset)
            )

            plausible = (
                nasa_los_geometry[
                    "elevation"
                ] > 0
                and nasa_aos_geometry[
                    "elevation"
                ] > 0
            )

            independent_results.append(
                {
                    "station":
                        station_name,

                    "ingress":
                        ingress,

                    "egress":
                        egress,

                    "ingress_offset":
                        ingress_offset,

                    "egress_offset":
                        egress_offset,

                    "total_offset":
                        total_offset,

                    "los_elevation":
                        nasa_los_geometry[
                            "elevation"
                        ],

                    "aos_elevation":
                        nasa_aos_geometry[
                            "elevation"
                        ],

                    "occulted_at_los":
                        nasa_los_geometry[
                            "occulted"
                        ],

                    "occulted_at_aos":
                        nasa_aos_geometry[
                            "occulted"
                        ],

                    "plausible":
                        plausible,
                }
            )

        independent_results.sort(
            key=lambda row:
                row["total_offset"]
        )

        summary_results = {
            row["station"]:
                row
            for row in summary[
                "station_results"
            ]
        }

        for independent in (
            independent_results
        ):
            station_name = (
                independent["station"]
            )

            if station_name not in (
                summary_results
            ):
                fail(
                    f"{station_name} missing "
                    "from summary"
                )

            observed = (
                summary_results[
                    station_name
                ]
            )

            if abs(
                (
                    parse_utc(
                        observed["ingress_utc"]
                    )
                    - independent["ingress"]
                ).total_seconds()
            ) > 0.001:
                fail(
                    f"{station_name} ingress "
                    "summary mismatch"
                )

            if abs(
                (
                    parse_utc(
                        observed["egress_utc"]
                    )
                    - independent["egress"]
                ).total_seconds()
            ) > 0.001:
                fail(
                    f"{station_name} egress "
                    "summary mismatch"
                )

            if abs(
                float(
                    observed[
                        "orion_elevation_deg_at_nasa_los"
                    ]
                )
                - independent[
                    "los_elevation"
                ]
            ) > 1e-6:
                fail(
                    f"{station_name} LOS "
                    "elevation mismatch"
                )

            if abs(
                float(
                    observed[
                        "orion_elevation_deg_at_nasa_aos"
                    ]
                )
                - independent[
                    "aos_elevation"
                ]
            ) > 1e-6:
                fail(
                    f"{station_name} AOS "
                    "elevation mismatch"
                )

        plausible = [
            row["station"]
            for row in independent_results
            if row["plausible"]
        ]

        expectations = (
            reference[
                "inspection_expectations"
            ]
        )

        expected_plausible = (
            expectations[
                "expected_only_reference_station_above_horizon_at_both_nasa_contacts"
            ]
        )

        if plausible != [
            expected_plausible
        ]:
            fail(
                "unexpected horizon-plausible "
                "reference station set"
            )

        best = (
            independent_results[0]
        )

        if (
            best["station"]
            != "DSS-43"
        ):
            fail(
                "DSS-43 no longer has best "
                "pure geometric timing agreement"
            )

        if (
            best["total_offset"]
            > float(
                expectations[
                    "maximum_dss43_total_absolute_nasa_contact_offset_seconds"
                ]
            )
        ):
            fail(
                "DSS-43 timing offset exceeds "
                "validation threshold"
            )

        improvement = (
            (
                geocentric_total_offset
                - best["total_offset"]
            )
            / geocentric_total_offset
        )

        if improvement < float(
            expectations[
                "minimum_dss43_timing_improvement_fraction_vs_geocentric"
            ]
        ):
            fail(
                "topocentric timing improvement "
                "below expected threshold"
            )

        if not best[
            "occulted_at_los"
        ]:
            fail(
                "DSS-43 must be occulted "
                "at NASA LOS"
            )

        if best[
            "occulted_at_aos"
        ]:
            fail(
                "DSS-43 must be clear "
                "at NASA AOS"
            )

        if (
            summary[
                "operational_station_assignment_inferred"
            ]
            is not False
        ):
            fail(
                "summary improperly claims "
                "operational station assignment"
            )

        if (
            summary["guardrails"]
            != reference["guardrails"]
        ):
            fail(
                "guardrails changed"
            )

        if not OUTPUT_CSV.exists():
            fail(
                "sampled geometry CSV missing"
            )

        with OUTPUT_CSV.open(
            "r",
            encoding="utf-8-sig",
        ) as f:
            rows = list(
                csv.DictReader(f)
            )

        expected_grid_count = (
            int(
                (
                    stop - start
                ).total_seconds()
                / step
            )
            + 1
        )

        expected_csv_rows = (
            expected_grid_count
            * 3
        )

        if len(rows) != expected_csv_rows:
            fail(
                "unexpected sampled geometry "
                "row count"
            )

        for figure in [
            OCCULTATION_FIGURE,
            ELEVATION_FIGURE,
        ]:
            if not figure.exists():
                fail(
                    f"missing figure {figure}"
                )

            text = figure.read_text(
                encoding="utf-8"
            )

            if (
                "<svg" not in text
                or len(text) < 1000
            ):
                fail(
                    f"invalid figure {figure}"
                )

        print()
        print(
            "Phase 2G.2 Topocentric DSN "
            "Geometry Validation"
        )

        print("=" * 54)

        print()
        print(
            "Independent reference stations:"
        )

        for result in (
            independent_results
        ):
            print()
            print(
                f"  {result['station']}"
            )

            print(
                "    ingress:"
            )

            print(
                "      "
                f"{result['ingress'].isoformat()}"
            )

            print(
                "    egress:"
            )

            print(
                "      "
                f"{result['egress'].isoformat()}"
            )

            print(
                "    NASA LOS elevation:"
            )

            print(
                "      "
                f"{result['los_elevation']:.3f} deg"
            )

            print(
                "    NASA AOS elevation:"
            )

            print(
                "      "
                f"{result['aos_elevation']:.3f} deg"
            )

            print(
                "    total absolute NASA "
                "timing offset:"
            )

            print(
                "      "
                f"{result['total_offset']:.3f} s"
            )

            print(
                "    horizon plausible:"
            )

            print(
                "      "
                f"{result['plausible']}"
            )

        print()
        print(
            "Derived geometric result:"
        )

        print(
            "  only reference station above "
            "horizon at both NASA contacts:"
        )

        print(
            "    DSS-43"
        )

        print(
            "  best pure timing agreement:"
        )

        print(
            "    DSS-43"
        )

        print(
            "  timing improvement vs "
            "Earth-center model:"
        )

        print(
            "    "
            f"{100.0 * improvement:.3f}%"
        )

        print()
        print(
            "Operational assignment:"
        )

        print(
            "  NOT INFERRED"
        )

        print()
        print(
            "Products:"
        )

        print(
            f"  sampled rows: {len(rows)}"
        )

        print(
            "  summary: PASS"
        )

        print(
            "  occultation figure: PASS"
        )

        print(
            "  elevation figure: PASS"
        )

        print()
        print(
            "OK: Phase 2G.2 NAIF station "
            "coordinates, plate motion, Earth "
            "orientation, topocentric lunar "
            "occultation, local horizon geometry, "
            "NASA timing comparison, generated "
            "products, and non-assignment "
            "guardrails independently validated."
        )

    finally:
        spice.kclear()


if __name__ == "__main__":
    main()