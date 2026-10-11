from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

REFERENCE_JSON = (
    ROOT
    / "data"
    / "reference"
    / "artemis_ii_entry_events.json"
)

RESULT_JSON = (
    ROOT
    / "data"
    / "processed"
    / "entry"
    / "entry_event_correlations.json"
)

ASSET_DIR = (
    ROOT
    / "docs"
    / "assets"
    / "entry"
)


def fail(
    message: str,
):
    raise SystemExit(
        "VALIDATION FAILED: "
        f"{message}"
    )


def main():
    if not REFERENCE_JSON.exists():
        fail(
            "NASA event reference missing"
        )

    if not RESULT_JSON.exists():
        fail(
            "event-correlation output missing"
        )

    with REFERENCE_JSON.open(
        "r",
        encoding="utf-8",
    ) as f:
        reference = json.load(f)

    with RESULT_JSON.open(
        "r",
        encoding="utf-8",
    ) as f:
        result = json.load(f)

    events = {
        event[
            "event_id"
        ]: event
        for event in reference[
            "events"
        ]
    }

    expected_ids = {
        "entry_interface",
        "drogue_deploy",
        "main_deploy",
        "splashdown",
    }

    if set(
        events
    ) != expected_ids:
        fail(
            "unexpected NASA event IDs"
        )

    # --------------------------------------------------------
    # Minute-level time correlation
    # --------------------------------------------------------

    for event_id in [
        "entry_interface",
        "drogue_deploy",
        "main_deploy",
        "splashdown",
    ]:
        if not result[
            event_id
        ][
            "within_reported_minute"
        ]:
            fail(
                f"{event_id} does not "
                "fall within NASA's "
                "reported minute"
            )

    # --------------------------------------------------------
    # Entry Interface validation
    # --------------------------------------------------------

    ei = result[
        "entry_interface"
    ]

    if abs(
        ei[
            "altitude_difference_m"
        ]
    ) > 1.0:
        fail(
            "EI altitude differs by "
            "more than 1 meter"
        )

    if abs(
        ei[
            "distance_percent_difference"
        ]
    ) > 1.0:
        fail(
            "EI-to-terminal distance differs "
            "from NASA's approximate value "
            "by more than 1 percent"
        )

    # --------------------------------------------------------
    # Drogue sequence
    # --------------------------------------------------------

    drogue = result[
        "drogue_deploy"
    ]

    speed_offset = abs(
        drogue[
            "speed_crossing_offset_from_altitude_anchor_seconds"
        ]
    )

    if speed_offset > 2.0:
        fail(
            "479-ft/s crossing is not "
            "closely aligned with the "
            "23,400-ft drogue anchor"
        )

    # Do NOT require the 0.8-mile condition
    # to occur at deployment. The public
    # update is not treated as an exact
    # synchronous telemetry tuple.
    distance_offset = (
        drogue[
            "distance_crossing_offset_from_altitude_anchor_seconds"
        ]
    )

    if distance_offset is None:
        fail(
            "0.8-mile condition was not "
            "found in the trajectory"
        )

    # --------------------------------------------------------
    # Main parachute sequence
    # --------------------------------------------------------

    main = result[
        "main_deploy"
    ]

    speed_response = (
        main[
            "speed_response_offset_seconds"
        ]
    )

    if not (
        0.0
        <= speed_response
        <= 10.0
    ):
        fail(
            "200-ft/s threshold does not "
            "follow the 5,400-ft anchor "
            "within a plausible short "
            "trajectory interval"
        )

    # --------------------------------------------------------
    # Splashdown correlation
    # --------------------------------------------------------

    splash = result[
        "splashdown"
    ]

    if (
        splash[
            "classification"
        ]
        !=
        "DERIVED_SPLASHDOWN_CORRELATED_SURFACE_CROSSING"
    ):
        fail(
            "unexpected splashdown "
            "classification"
        )

    derived = splash[
        "derived_surface_crossing"
    ]

    if abs(
        derived[
            "wgs84_altitude_km"
        ]
    ) > 1e-6:
        fail(
            "derived splashdown-correlated "
            "state is not at WGS84 "
            "zero-altitude crossing"
        )

    if not (
        5.0
        <= splash[
            "derived_surface_speed_m_s"
        ]
        <= 15.0
    ):
        fail(
            "terminal Earth-relative speed "
            "outside expected trajectory "
            "sanity range"
        )

    # --------------------------------------------------------
    # Figures
    # --------------------------------------------------------

    expected_assets = [
        (
            ASSET_DIR
            / "phase2d_entry_events_altitude.svg"
        ),
        (
            ASSET_DIR
            / "phase2d_terminal_ground_track.svg"
        ),
    ]

    for asset in expected_assets:
        if not asset.exists():
            fail(
                f"missing documentation "
                f"asset: {asset}"
            )

    print()
    print(
        "Artemis II Entry "
        "Event Correlation Validation"
    )

    print(
        "--------------------------------"
    )

    print()
    print(
        "Minute-level NASA event matches:"
    )

    print(
        "  Entry Interface: PASS"
    )

    print(
        "  Drogues:         PASS"
    )

    print(
        "  Mains:           PASS"
    )

    print(
        "  Splashdown:      PASS"
    )

    print()
    print(
        "Entry Interface:"
    )

    print(
        "  altitude difference: "
        f"{ei['altitude_difference_m']:+.3f} m"
    )

    print(
        "  distance difference: "
        f"{ei['distance_percent_difference']:+.4f}%"
    )

    print()
    print(
        "Drogue sequence:"
    )

    print(
        "  479-ft/s crossing offset: "
        f"{drogue['speed_crossing_offset_from_altitude_anchor_seconds']:+.6f} s"
    )

    print(
        "  0.8-mi crossing offset: "
        f"{distance_offset:+.6f} s"
    )

    print(
        "  NOTE: 0.8-mi value is not "
        "used as a synchronous "
        "deployment-state constraint."
    )

    print()
    print(
        "Main sequence:"
    )

    print(
        "  200-ft/s response offset: "
        f"{speed_response:+.6f} s"
    )

    print()
    print(
        "Splashdown correlation:"
    )

    print(
        "  UTC: "
        f"{derived['utc']}"
    )

    print(
        "  latitude: "
        f"{derived['latitude_deg']:.6f} deg"
    )

    print(
        "  longitude: "
        f"{derived['longitude_deg']:.6f} deg"
    )

    print(
        "  Earth-relative speed: "
        f"{splash['derived_surface_speed_m_s']:.3f} m/s"
    )

    print()
    print(
        "OK: NASA entry-event timing, "
        "reported-condition alignment, "
        "and splashdown correlation "
        "validated."
    )

    print()
    print(
        "NOTE: Derived sub-second epochs "
        "are not official NASA event "
        "timestamps."
    )


if __name__ == "__main__":
    main()