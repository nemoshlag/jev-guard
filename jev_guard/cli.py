"""Command line interface: `jev-guard scan` and `jev-guard serve`."""

from __future__ import annotations

import argparse
import sys

from jev_guard.config import Settings
from jev_guard.detectors import ClassifierError
from jev_guard.guard import Guard


def _scan(args: argparse.Namespace) -> int:
    text = sys.stdin.read() if args.file == "-" else open(args.file, encoding="utf-8").read()
    guard = Guard.from_settings(Settings.from_env())
    try:
        result = guard.scan(text, redact_text=args.redact)
    except ClassifierError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    finally:
        guard.close()
    if args.redact:
        sys.stdout.write(result.redacted_text or "")
    else:
        print(result.model_dump_json(indent=2))
    return 1 if result.has_pii else 0


def _serve(args: argparse.Namespace) -> int:
    import uvicorn

    uvicorn.run("jev_guard.api:create_app", factory=True, host=args.host, port=args.port)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="jev-guard", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    scan = sub.add_parser("scan", help="Scan a file (or - for stdin). Exit 1 if PII is found.")
    scan.add_argument("file")
    scan.add_argument("--redact", action="store_true", help="Print redacted text instead of JSON")
    scan.set_defaults(func=_scan)

    serve = sub.add_parser("serve", help="Run the REST API")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8080)
    serve.set_defaults(func=_serve)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
