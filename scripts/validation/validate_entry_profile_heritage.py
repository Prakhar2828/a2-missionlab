from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[2]

REFERENCE_JSON = (
    ROOT
    / "data"
    / "reference"
    / "artemis_entry_profile_heritage.json"
)


EXPECTED_DATASET_ID = (
    "phase2f2_artemis_entry_profile_heritage"
)

EXPECTED_PROVENANCE = "NASA_REPORTED"

EXPECTED_EVIDENCE_IDS = {
    "artemis_i_entry_interface_state",
    "artemis_i_skip_apogee",
    "artemis_i_sensed_acceleration_peaks",
    "artemis_i_ei_to_splashdown_duration",
    "artemis_ii_no_skip_entry",
    "artemis_ii_lofted_entry_label",
    "artemis_ii_public_pre_ei_velocity",
}

ALLOWED_HOSTS = {
    "ntrs.nasa.gov",
    "www.nasa.gov",
    "nasa.gov",
}

REQUIRED_GUARDRAILS = {
    "Artemis II must not be labeled a skip entry.",
    (
        "The Artemis II derived vertical rebound may be "
        "described as a rebound or loft."
    ),
    (
        "Artemis I skip-apogee altitude and Artemis II "
        "rebound-top altitude may be compared as upper-profile "
        "landmarks but not as identical guidance phases."
    ),
    (
        "The Artemis I to Artemis II duration comparison must "
        "preserve mixed provenance between NASA-reported "
        "Artemis I epochs and the MissionLab-derived Artemis II "
        "surface crossing."
    ),
    (
        "Public mission velocity figures are context only when "
        "epoch or frame semantics are not matched."
    ),
    (
        "The primary speed comparison must use inertial velocity "
        "magnitudes with explicitly compatible semantics."
    ),
    (
        "Artemis I sensed acceleration must not be directly "
        "compared with Phase 2C MissionLab g0-equivalent "
        "kinematic deceleration."
    ),
    (
        "No trajectory comparison may be converted into a TPS "
        "char-loss or damage prediction."
    ),
    (
        "No causal claim may be made that every Artemis I versus "
        "Artemis II entry-profile difference was driven exclusively "
        "by the heat-shield investigation."
    ),
}


def fail(
    message: str,
) -> None:
    raise SystemExit(
        "VALIDATION FAILED: "
        f"{message}"
    )


def require_string(
    value,
    label: str,
) -> None:
    if not isinstance(
        value,
        str,
    ):
        fail(
            f"{label} must be a string"
        )

    if not value.strip():
        fail(
            f"{label} must not be empty"
        )


def validate_date(
    value,
    evidence_id: str,
) -> None:
    if value is None:
        return

    if not isinstance(
        value,
        str,
    ):
        fail(
            f"{evidence_id}: "
            "source_date must be null, YYYY, "
            "or YYYY-MM-DD"
        )

    if (
        len(value) == 4
        and value.isdigit()
    ):
        year = int(
            value
        )

        if not (
            1900
            <= year
            <= 2100
        ):
            fail(
                f"{evidence_id}: "
                f"invalid year {value!r}"
            )

        return

    try:
        date.fromisoformat(
            value
        )
    except ValueError:
        fail(
            f"{evidence_id}: "
            f"invalid source_date {value!r}"
        )


def validate_url(
    value,
    evidence_id: str,
) -> None:
    require_string(
        value,
        f"{evidence_id}.source_url",
    )

    parsed = urlparse(
        value
    )

    if parsed.scheme != "https":
        fail(
            f"{evidence_id}: "
            "source URL must use HTTPS"
        )

    host = (
        parsed.hostname
        or ""
    ).lower()

    if host not in ALLOWED_HOSTS:
        fail(
            f"{evidence_id}: "
            f"unexpected source host "
            f"{host!r}"
        )


def main() -> None:
    if not REFERENCE_JSON.exists():
        fail(
            "missing entry-profile heritage "
            f"reference: {REFERENCE_JSON}"
        )

    try:
        with REFERENCE_JSON.open(
            "r",
            encoding="utf-8-sig",
        ) as f:
            dataset = json.load(
                f
            )
    except json.JSONDecodeError as exc:
        fail(
            f"invalid JSON: {exc}"
        )

    if (
        dataset.get(
            "dataset_id"
        )
        != EXPECTED_DATASET_ID
    ):
        fail(
            "unexpected dataset_id"
        )

    if (
        dataset.get(
            "provenance"
        )
        != EXPECTED_PROVENANCE
    ):
        fail(
            "unexpected top-level provenance"
        )

    require_string(
        dataset.get(
            "scope"
        ),
        "scope",
    )

    evidence = dataset.get(
        "evidence_items"
    )

    if not isinstance(
        evidence,
        list,
    ):
        fail(
            "evidence_items must be a list"
        )

    if len(
        evidence
    ) != len(
        EXPECTED_EVIDENCE_IDS
    ):
        fail(
            "unexpected evidence-item count"
        )

    ids = []

    source_urls = set()
    source_hosts = set()

    for index, item in enumerate(
        evidence
    ):
        if not isinstance(
            item,
            dict,
        ):
            fail(
                f"evidence item {index} "
                "must be an object"
            )

        evidence_id = item.get(
            "id"
        )

        require_string(
            evidence_id,
            f"evidence_items[{index}].id",
        )

        ids.append(
            evidence_id
        )

        for field in [
            "mission",
            "category",
            "claim",
            "provenance",
            "source_title",
            "source_url",
            "source_organization",
            "interpretation",
        ]:
            require_string(
                item.get(
                    field
                ),
                f"{evidence_id}.{field}",
            )

        if (
            item[
                "provenance"
            ]
            != EXPECTED_PROVENANCE
        ):
            fail(
                f"{evidence_id}: "
                "unexpected provenance"
            )

        validate_url(
            item[
                "source_url"
            ],
            evidence_id,
        )

        validate_date(
            item.get(
                "source_date"
            ),
            evidence_id,
        )

        limitations = item.get(
            "limitations"
        )

        if not isinstance(
            limitations,
            list,
        ):
            fail(
                f"{evidence_id}: "
                "limitations must be a list"
            )

        if not limitations:
            fail(
                f"{evidence_id}: "
                "limitations must not be empty"
            )

        for limitation in limitations:
            require_string(
                limitation,
                f"{evidence_id}.limitation",
            )

        source_urls.add(
            item[
                "source_url"
            ]
        )

        source_hosts.add(
            (
                urlparse(
                    item[
                        "source_url"
                    ]
                ).hostname
                or ""
            ).lower()
        )

    if len(
        ids
    ) != len(
        set(
            ids
        )
    ):
        fail(
            "duplicate evidence IDs"
        )

    if set(
        ids
    ) != EXPECTED_EVIDENCE_IDS:
        fail(
            "evidence ID inventory mismatch"
        )

    by_id = {
        item[
            "id"
        ]: item
        for item in evidence
    }

    ar1_ei = by_id[
        "artemis_i_entry_interface_state"
    ][
        "key_values"
    ]

    if (
        ar1_ei[
            "geodetic_altitude_ft"
        ]
        != 400000.0
    ):
        fail(
            "unexpected Artemis I EI altitude"
        )

    if abs(
        ar1_ei[
            "inertial_velocity_magnitude_ft_s"
        ]
        - 36062.6568
    ) > 1e-7:
        fail(
            "unexpected Artemis I EI "
            "inertial velocity"
        )

    skip = by_id[
        "artemis_i_skip_apogee"
    ][
        "key_values"
    ]

    if (
        skip[
            "entry_classification"
        ]
        != "SKIP_ENTRY"
    ):
        fail(
            "Artemis I must remain "
            "classified as SKIP_ENTRY"
        )

    if abs(
        skip[
            "actual_skip_apogee_kft"
        ]
        - 287.4
    ) > 1e-12:
        fail(
            "unexpected Artemis I "
            "skip apogee"
        )

    if abs(
        skip[
            "actual_skip_apogee_km"
        ]
        - 87.59952
    ) > 1e-9:
        fail(
            "unexpected converted "
            "skip-apogee altitude"
        )

    acceleration = by_id[
        "artemis_i_sensed_acceleration_peaks"
    ][
        "key_values"
    ]

    if (
        acceleration[
            "first_peak_sensed_acceleration_g"
        ]
        != 4.05
    ):
        fail(
            "unexpected first Artemis I "
            "sensed-acceleration peak"
        )

    if (
        acceleration[
            "second_peak_sensed_acceleration_g"
        ]
        != 3.89
    ):
        fail(
            "unexpected second Artemis I "
            "sensed-acceleration peak"
        )

    duration = by_id[
        "artemis_i_ei_to_splashdown_duration"
    ][
        "key_values"
    ]

    if (
        duration[
            "entry_interface_met"
        ]
        != "025/11:15:52"
    ):
        fail(
            "unexpected Artemis I EI MET"
        )

    if (
        duration[
            "splashdown_met"
        ]
        != "025/11:36:27"
    ):
        fail(
            "unexpected Artemis I "
            "splashdown MET"
        )

    if (
        duration[
            "ei_to_splashdown_seconds"
        ]
        != 1235.0
    ):
        fail(
            "unexpected Artemis I "
            "entry duration"
        )

    ar2_classification = by_id[
        "artemis_ii_no_skip_entry"
    ][
        "key_values"
    ][
        "entry_classification"
    ]

    if (
        ar2_classification
        != "MODIFIED_TRAJECTORY_WITHOUT_SKIP_ENTRY"
    ):
        fail(
            "Artemis II no-skip "
            "classification changed"
        )

    loft_label = by_id[
        "artemis_ii_lofted_entry_label"
    ][
        "key_values"
    ][
        "public_profile_label"
    ]

    if (
        loft_label
        != "LOFTED_ENTRY_SEQUENCE"
    ):
        fail(
            "unexpected Artemis II "
            "public profile label"
        )

    public_speed = by_id[
        "artemis_ii_public_pre_ei_velocity"
    ][
        "key_values"
    ][
        "maximum_velocity_before_ei_mph"
    ]

    if (
        public_speed
        != 23864.0
    ):
        fail(
            "unexpected Artemis II "
            "public pre-EI velocity"
        )

    plan = dataset.get(
        "permanent_comparison_plan"
    )

    if not isinstance(
        plan,
        dict,
    ):
        fail(
            "missing permanent comparison plan"
        )

    primary_metrics = plan.get(
        "primary_metrics"
    )

    if not isinstance(
        primary_metrics,
        list,
    ):
        fail(
            "primary_metrics must be a list"
        )

    if len(
        primary_metrics
    ) != 5:
        fail(
            "expected five primary "
            "comparison metrics"
        )

    planned_figures = dataset.get(
        "planned_figures"
    )

    if not isinstance(
        planned_figures,
        list,
    ):
        fail(
            "planned_figures must be a list"
        )

    if len(
        planned_figures
    ) != 3:
        fail(
            "expected three planned figures"
        )

    expected_figure_names = {
        "phase2f_entry_duration_comparison.svg",
        "phase2f_skip_loft_altitude_comparison.svg",
        "phase2f_artemis_ii_rebound_profile.svg",
    }

    observed_figure_names = {
        item.get(
            "filename"
        )
        for item in planned_figures
    }

    if (
        observed_figure_names
        != expected_figure_names
    ):
        fail(
            "planned figure inventory mismatch"
        )

    guardrails = dataset.get(
        "interpretation_guardrails"
    )

    if not isinstance(
        guardrails,
        list,
    ):
        fail(
            "interpretation_guardrails "
            "must be a list"
        )

    if set(
        guardrails
    ) != REQUIRED_GUARDRAILS:
        fail(
            "interpretation guardrails "
            "do not match expected set"
        )

    print()
    print(
        "Artemis Entry-Profile Heritage "
        "Validation"
    )

    print(
        "--------------------------------"
    )

    print(
        f"Evidence items checked: "
        f"{len(evidence)}"
    )

    print(
        f"Unique source URLs: "
        f"{len(source_urls)}"
    )

    print(
        "Source hosts:"
    )

    for host in sorted(
        source_hosts
    ):
        print(
            f"  {host}"
        )

    print()
    print(
        "Artemis I reference invariants:"
    )

    print(
        "  EI altitude: "
        "400000.0 ft"
    )

    print(
        "  EI inertial speed: "
        "36062.65680 ft/s"
    )

    print(
        "  Skip apogee: "
        "287.40 kft"
    )

    print(
        "  Sensed acceleration peaks: "
        "4.05 g / 3.89 g"
    )

    print(
        "  EI to splashdown: "
        "1235.0 s"
    )

    print()
    print(
        "Artemis II terminology:"
    )

    print(
        "  NASA classification: "
        "MODIFIED TRAJECTORY WITHOUT SKIP ENTRY"
    )

    print(
        "  NASA public label: "
        "LOFTED ENTRY SEQUENCE"
    )

    print()
    print(
        "Comparison guardrails:"
    )

    print(
        "  Artemis II skip-entry label: "
        "PROHIBITED"
    )

    print(
        "  Sensed-g vs kinematic-g0 "
        "comparison: PROHIBITED"
    )

    print(
        "  Direct trajectory-to-TPS-damage "
        "inference: PROHIBITED"
    )

    print()
    print(
        "OK: Artemis entry-profile heritage "
        "evidence, numerical invariants, "
        "comparison plan, and terminology "
        "guardrails validated."
    )


if __name__ == "__main__":
    main()