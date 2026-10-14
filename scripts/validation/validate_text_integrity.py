from __future__ import annotations

import re
from html.parser import HTMLParser
from pathlib import Path


ROOT = (
    Path(__file__)
    .resolve()
    .parents[2]
)


PUBLIC_HTML = [
    "index.html",
    "mission.html",
    "windows.html",
    "gnc.html",
    "mission-control.html",
    "psi.html",
    "library.html",
    "technical-report.html",
]


PUBLIC_TEXT = [
    *PUBLIC_HTML,
    "styles.css",
    "responsive-hardening.css",
    "landing.css",
    "windows.css",
    "gnc.css",
    "mission-control.css",
    "psi.css",
    "trajectory.css",
    "space-weather.css",
    "app.js",
    "library.js",
    "js/core.js",
    "js/mission.js",
    "js/windows.js",
    "js/gnc.js",
    "js/mission-control.js",
    "js/psi-model.js",
    "js/psi.js",
    "js/trajectory-model.js",
    "js/trajectory.js",
    "js/space-weather-model.js",
    "js/space-weather.js",
]


MOJIBAKE = (
    "\ufffd",
    "\u00c3",
    "\u00c2",
    "\u00e2\u20ac",
    "\u00f0\u0178",
)


SUSPICIOUS_HTML_PATTERNS = (
    (
        re.compile(
            r" \? "
        ),
        (
            "space-delimited placeholder "
            "question mark"
        ),
    ),
    (
        re.compile(
            r">\s*\?\s*<"
        ),
        (
            "standalone question-mark "
            "UI glyph"
        ),
    ),
    (
        re.compile(
            r"\d\?\s"
        ),
        (
            "digit followed by placeholder "
            "question mark"
        ),
    ),
)


failures: list[str] = []


class AuditParser(
    HTMLParser
):

    def __init__(
        self,
    ) -> None:

        super().__init__(
            convert_charrefs=True
        )

        self.ids: list[str] = []
        self.h1_count = 0
        self.labels_for: set[str] = set()
        self.inputs = []
        self.canvases = []
        self.buttons = []
        self.images = []
        self.blank_links = []

    def handle_starttag(
        self,
        tag: str,
        attrs,
    ) -> None:

        a = dict(attrs)

        element_id = a.get(
            "id"
        )

        if element_id:

            self.ids.append(
                element_id
            )

        if tag == "h1":

            self.h1_count += 1

        elif tag == "label":

            target = a.get(
                "for"
            )

            if target:

                self.labels_for.add(
                    target
                )

        elif tag == "input":

            self.inputs.append(a)

        elif tag == "canvas":

            self.canvases.append(a)

        elif tag == "button":

            self.buttons.append(a)

        elif tag == "img":

            self.images.append(a)

        elif (
            tag == "a"
            and a.get("target")
            == "_blank"
        ):

            self.blank_links.append(a)


def fail(
    rel: str,
    message: str,
) -> None:

    failures.append(
        f"{rel}: {message}"
    )


for rel in PUBLIC_TEXT:

    path = ROOT / rel

    if not path.is_file():

        fail(
            rel,
            "missing public text file",
        )

        continue

    raw = path.read_bytes()

    if raw.startswith(
        b"\xef\xbb\xbf"
    ):

        fail(
            rel,
            "UTF-8 BOM is not allowed",
        )

    try:

        text = raw.decode(
            "utf-8"
        )

    except UnicodeDecodeError as exc:

        fail(
            rel,
            f"not valid UTF-8: {exc}",
        )

        continue

    for marker in MOJIBAKE:

        if marker in text:

            fail(
                rel,
                (
                    "contains mojibake "
                    "marker "
                    + repr(marker)
                ),
            )


for rel in PUBLIC_HTML:

    path = ROOT / rel

    if not path.is_file():

        continue

    text = path.read_text(
        encoding="utf-8"
    )

    for pattern, label in (
        SUSPICIOUS_HTML_PATTERNS
    ):

        match = pattern.search(
            text
        )

        if match:

            line = (
                text.count(
                    "\n",
                    0,
                    match.start(),
                )
                + 1
            )

            fail(
                rel,
                f"{label} at line {line}",
            )

    if (
        '<meta charset="utf-8">'
        not in text.lower()
    ):

        fail(
            rel,
            (
                "missing UTF-8 charset "
                "declaration"
            ),
        )

    if (
        'name="viewport"'
        not in text
    ):

        fail(
            rel,
            "missing viewport meta tag",
        )

    if not re.search(
        r"<title>\s*\S.*?</title>",
        text,
        re.I | re.S,
    ):

        fail(
            rel,
            "missing/non-empty title",
        )

    parser = AuditParser()

    try:

        parser.feed(
            text
        )

    except Exception as exc:

        fail(
            rel,
            f"HTML parser error: {exc}",
        )

        continue

    counts: dict[str, int] = {}

    for element_id in parser.ids:

        counts[element_id] = (
            counts.get(
                element_id,
                0,
            )
            + 1
        )

    duplicates = sorted(
        element_id
        for element_id, count
        in counts.items()
        if count > 1
    )

    if duplicates:

        fail(
            rel,
            (
                "duplicate IDs: "
                + ", ".join(
                    duplicates
                )
            ),
        )

    if parser.h1_count != 1:

        fail(
            rel,
            (
                "expected exactly one H1, "
                f"found {parser.h1_count}"
            ),
        )

    for attrs in parser.images:

        if "alt" not in attrs:

            fail(
                rel,
                (
                    "img missing alt: "
                    + (
                        attrs.get("src")
                        or "<no src>"
                    )
                ),
            )

    for attrs in parser.buttons:

        if not attrs.get(
            "type"
        ):

            fail(
                rel,
                (
                    "button missing "
                    "explicit type: #"
                    + (
                        attrs.get("id")
                        or "<no id>"
                    )
                ),
            )

    for attrs in parser.inputs:

        input_id = attrs.get(
            "id"
        )

        accessible = bool(
            attrs.get(
                "aria-label"
            )
        )

        if (
            input_id
            and input_id
            in parser.labels_for
        ):

            accessible = True

        if not accessible:

            fail(
                rel,
                (
                    "input missing "
                    "label/aria-label: #"
                    + (
                        input_id
                        or "<no id>"
                    )
                ),
            )

    for attrs in parser.canvases:

        named = bool(
            attrs.get(
                "aria-label"
            )
        )

        hidden = (
            attrs.get(
                "aria-hidden"
            )
            == "true"
        )

        if not (
            named
            or hidden
        ):

            fail(
                rel,
                (
                    "canvas missing "
                    "aria-label/aria-hidden: #"
                    + (
                        attrs.get("id")
                        or "<no id>"
                    )
                ),
            )

    for attrs in parser.blank_links:

        rel_tokens = {
            token.lower()
            for token
            in (
                attrs.get("rel")
                or ""
            ).split()
        }

        if not {
            "noopener",
            "noreferrer",
        }.issubset(
            rel_tokens
        ):

            fail(
                rel,
                (
                    "target=_blank link "
                    "missing "
                    "noopener+noreferrer: "
                    + (
                        attrs.get("href")
                        or "<no href>"
                    )
                ),
            )


print(
    "A2 MissionLab public "
    "text / markup integrity"
)

print(
    "=" * 58
)


if failures:

    for item in failures:

        print(
            "FAIL:",
            item,
        )

    print(
        f"\nRESULT: FAIL "
        f"({len(failures)} issue(s))"
    )

    raise SystemExit(1)


print(
    f"PASS: {len(PUBLIC_TEXT)} "
    "public text sources are strict UTF-8"
)

print(
    f"PASS: {len(PUBLIC_HTML)} "
    "public HTML routes have no "
    "placeholder glyph corruption"
)

print(
    "PASS: HTML structural and "
    "accessibility hygiene checks"
)

print(
    "\nRESULT: PASS"
)
