from __future__ import annotations

from pathlib import Path
import ast
import sys


REQUIRED = [
    "app.py",
    "ai_backend.py",
    "prompts.py",
    "report_parser.py",
    "requirements.txt",
]


def main():
    root = Path(__file__).resolve().parent

    missing = [
        filename
        for filename in REQUIRED
        if not (root / filename).exists()
    ]

    if missing:
        print("FAIL - missing files:", ", ".join(missing))
        return 1

    for filename in [
        "app.py",
        "ai_backend.py",
        "prompts.py",
        "report_parser.py",
    ]:
        source = (root / filename).read_text(encoding="utf-8")
        ast.parse(source, filename=filename)

    app_source = (root / "app.py").read_text(encoding="utf-8")

    forbidden = [
        "from techcheck.",
        "import techcheck",
        "replace_with_server_side_key",
        "use_container_width",
    ]

    found = [
        value
        for value in forbidden
        if value in app_source
    ]

    if found:
        print("FAIL - obsolete code found:", found)
        return 1

    print("PASS - project structure and Python syntax are valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
