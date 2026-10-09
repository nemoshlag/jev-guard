"""End-to-end demo: mock classifier + guard API + sample texts.

    uv run python demo/demo.py

Starts both servers on loopback, scans the samples through the real REST API, prints a table.
"""

from __future__ import annotations

import os
import subprocess
import sys
import time

import httpx

KEY = "demo-key"
GUARD, MOCK = "http://127.0.0.1:18080", "http://127.0.0.1:18009"

SAMPLES = [
    ("Clean text", "The quarterly report is due on Friday."),
    ("Regex-detectable", "Email jane.doe@example.com, card 4111 1111 1111 1111."),
    ("Context-only (regex misses)", "My name is Alice Smith and she lives at the old mill."),
    ("Both", "My name is Bob, reach me at bob@example.org or +1 415-555-2671."),
]


def wait(url: str) -> None:
    for _ in range(50):
        try:
            httpx.get(url, timeout=1)
            return
        except httpx.HTTPError:
            time.sleep(0.2)
    raise SystemExit(f"timeout waiting for {url}")


def main() -> None:
    env = {
        **os.environ,
        "JEV_GUARD_API_KEY": KEY,
        "JEV_GUARD_JEV_URL": MOCK,
        "JEV_GUARD_JEV_MODEL": "mock",
    }
    procs = [
        subprocess.Popen(  # noqa: S603
            [
                sys.executable,
                "-m",
                "uvicorn",
                "--app-dir",
                "demo",
                "mock_jev:app",
                "--port",
                "18009",
                "--log-level",
                "warning",
            ],
            env=env,
        ),
        subprocess.Popen(  # noqa: S603
            [sys.executable, "-m", "jev_guard.cli", "serve", "--port", "18080"],
            env=env,
        ),
    ]
    try:
        wait(f"{GUARD}/healthz")
        wait(f"{MOCK}/openapi.json")
        auth = {"Authorization": f"Bearer {KEY}"}
        print(f"{'sample':<30}{'PII?':<7}{'regex findings':<28}{'classifier'}")
        for label, text in SAMPLES:
            r = httpx.post(f"{GUARD}/v1/scan", json={"text": text, "redact": True}, headers=auth)
            r.raise_for_status()
            d = r.json()
            found = ",".join(sorted({f["entity_type"] for f in d["findings"]})) or "-"
            print(f"{label:<30}{'YES' if d['has_pii'] else 'no':<7}{found:<28}{d['classifier']}")
            print(f"    redacted: {d['redacted_text']}")
        no_auth = httpx.post(f"{GUARD}/v1/scan", json={"text": "x"})
        print(f"\nrequest without API key -> HTTP {no_auth.status_code}")
    finally:
        for p in procs:
            p.terminate()
            p.wait(timeout=10)


if __name__ == "__main__":
    main()
