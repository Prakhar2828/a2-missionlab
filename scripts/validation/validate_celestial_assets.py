from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

MANIFEST = (
    ROOT
    / "assets"
    / "public"
    / "celestial"
    / "manifest.json"
)


def sha256(path: Path) -> str:
    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def jpeg_dimensions(path: Path):
    data = path.read_bytes()

    if len(data) < 4:
        raise RuntimeError(
            f"{path} is too small"
        )

    if data[:2] != b"\xff\xd8":
        raise RuntimeError(
            f"{path} is not a JPEG"
        )

    sof_markers = {
        0xC0, 0xC1, 0xC2, 0xC3,
        0xC5, 0xC6, 0xC7,
        0xC9, 0xCA, 0xCB,
        0xCD, 0xCE, 0xCF,
    }

    i = 2

    while i < len(data):

        while (
            i < len(data)
            and data[i] != 0xFF
        ):
            i += 1

        while (
            i < len(data)
            and data[i] == 0xFF
        ):
            i += 1

        if i >= len(data):
            break

        marker = data[i]
        i += 1

        if marker in {
            0xD8,
            0xD9,
        }:
            continue

        if i + 2 > len(data):
            break

        segment_length = int.from_bytes(
            data[i:i+2],
            "big"
        )

        if segment_length < 2:
            break

        if marker in sof_markers:

            if i + 7 > len(data):
                break

            height = int.from_bytes(
                data[i+3:i+5],
                "big"
            )

            width = int.from_bytes(
                data[i+5:i+7],
                "big"
            )

            return width, height

        i += segment_length

    raise RuntimeError(
        f"Unable to read JPEG dimensions: {path}"
    )


def main() -> int:

    print(
        "Phase H celestial rendering asset validation"
    )

    print(
        "=" * 72
    )

    if not MANIFEST.is_file():
        print(
            "FAIL: celestial manifest missing"
        )

        return 1

    manifest = json.loads(
        MANIFEST.read_text(
            encoding="utf-8"
        )
    )

    if manifest.get(
        "schema_version"
    ) != 1:
        print(
            "FAIL: unexpected manifest schema"
        )

        return 1

    boundary = (
        manifest.get(
            "evidence_boundary",
            ""
        ).lower()
    )

    required_boundary = [
        "private telemetry",
        "exact artemis ii camera geometry",
        "timestamp-specific mission observations",
    ]

    for phrase in required_boundary:

        if phrase not in boundary:
            print(
                "FAIL: evidence boundary missing:",
                phrase
            )

            return 1

    assets = manifest.get(
        "assets",
        {}
    )

    for key in [
        "earth",
        "moon",
    ]:

        item = assets.get(
            key
        )

        if not item:
            print(
                f"FAIL: manifest missing {key}"
            )

            return 1

        path = (
            ROOT
            / item["path"]
        )

        if not path.is_file():
            print(
                f"FAIL: missing {key} asset:",
                path
            )

            return 1

        width, height = (
            jpeg_dimensions(
                path
            )
        )

        if (
            width
            != item["width"]
            or
            height
            != item["height"]
        ):
            print(
                f"FAIL: {key} dimensions changed: "
                f"{width}x{height}"
            )

            return 1

        if (
            path.stat().st_size
            != item["bytes"]
        ):
            print(
                f"FAIL: {key} file size changed"
            )

            return 1

        digest = sha256(
            path
        )

        if digest != item["sha256"]:
            print(
                f"FAIL: {key} SHA-256 changed"
            )

            return 1

        if width < 900 or height < 900:
            print(
                f"FAIL: {key} resolution too low"
            )

            return 1

        source_page = (
            item.get(
                "source_page",
                ""
            )
        )

        direct_source = (
            item.get(
                "direct_source",
                ""
            )
        )

        if (
            "nasa" not in source_page.lower()
            and
            "gsfc.nasa.gov"
            not in source_page.lower()
        ):
            print(
                f"FAIL: {key} source page is not NASA-hosted"
            )

            return 1

        if (
            "nasa" not in direct_source.lower()
            and
            "gsfc.nasa.gov"
            not in direct_source.lower()
        ):
            print(
                f"FAIL: {key} direct source is not NASA-hosted"
            )

            return 1

        print(
            f"PASS: {key}: "
            f"{width}x{height}, "
            f"{path.stat().st_size:,} bytes"
        )

        print(
            f"PASS: {key} SHA-256"
        )

        print(
            f"PASS: {key} NASA source metadata"
        )

    source_doc = (
        ROOT
        / "assets"
        / "public"
        / "IMAGE_SOURCES.md"
    ).read_text(
        encoding="utf-8"
    ).lower()

    required_doc = [
        "phase h celestial rendering assets",
        "pia18033",
        "nasa svs moon mosaic 5001",
        "1,231 lro narrow angle camera images",
        "visualization-only limb shading",
    ]

    for phrase in required_doc:

        if phrase not in source_doc:
            print(
                "FAIL: IMAGE_SOURCES.md missing:",
                phrase
            )

            return 1

    print(
        ""
    )

    print(
        "PASS: celestial rendering evidence boundary"
    )

    print(
        "PASS: repository-local NASA imagery provenance"
    )

    print(
        "PHASE H CELESTIAL ASSET VALIDATION PASSED"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
