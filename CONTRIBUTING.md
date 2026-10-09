# Contributing

1. Fork and branch from `main`.
2. `uv sync`, then make your change with tests.
3. `uv run pytest && uv run ruff check . && uv run ruff format --check .`
4. Open a PR describing the change.

Rules:
- Never commit real PII, secrets, or `.env` files. Use obviously fake test data.
- Never log request text or matched values.
- New categories (e.g. PCI, PHI) are added to `CATEGORY_QUESTIONS` in `jev_guard/detectors/jev.py`, with regex recognizers where applicable.

By contributing you agree your work is licensed under Apache-2.0. Be respectful; see the [Code of Conduct](CODE_OF_CONDUCT.md).
