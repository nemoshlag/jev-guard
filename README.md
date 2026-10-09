# jev-guard

Local PII detection that combines **regex detectors** ([Microsoft Presidio](https://github.com/microsoft/presidio) recognizers) with a **Jev-style classifier** for context-dependent PII that patterns can't catch. Run the classifier locally, or point at a remote endpoint, behind a small REST API / CLI / Docker Compose stack.

> Status: early (0.1). PCI and PHI categories are planned; the code is already category-driven.

## How it works

```
text ──► regex detectors (Presidio, offline) ──┐
     └─► classifier (System One API, noul)  ───┴─► has_pii + findings (offsets only) [+ redacted text]
```

- **Jev** is TypeSafe AI's hosted "System One" model: you send text plus typed questions (yes/no, choice, score) and get back calibrated probabilities. It is hosted-only.
- **[Kev](https://github.com/jaredpalmer/kev)** is an open (Apache-2.0), API-compatible implementation you can run locally. jev-guard speaks the System One API (`POST /v1/systemone`), so the same client works against a local Kev container or hosted Jev; only the URL changes.
- Regex hits and classifier probability (≥ threshold) are OR-ed. Findings contain offsets and entity types, never the matched text.

## Quick start

```bash
uv sync
echo "reach me at jane@example.com" | uv run jev-guard scan -   # exit 1 if PII found
uv run jev-guard scan notes.txt --redact
```

### Docker Compose

```bash
echo "JEV_GUARD_API_KEY=$(openssl rand -hex 32)" > .env      # required
docker compose up -d guard                                    # regex-only
docker compose --profile local-model up -d                    # + local Kev classifier (experimental)
```

```bash
curl -s localhost:8080/v1/scan -H "Authorization: Bearer $KEY" \
  -H 'content-type: application/json' -d '{"text":"mail jane@example.com","redact":true}'
```

### Configuration (environment / `.env`)

| Variable | Purpose |
|---|---|
| `JEV_GUARD_API_KEY` | Bearer key required by the guard API (required in compose) |
| `JEV_GUARD_JEV_URL` | Classifier endpoint; empty = regex-only. Local: `http://jev:8009` (with `JEV_GUARD_ALLOW_INSECURE_HTTP=true`, `JEV_GUARD_JEV_MODEL=kev-latest`). Hosted: `https://api.typesafe.ai` |
| `JEV_GUARD_JEV_API_KEY` | Key for the classifier endpoint |
| `JEV_GUARD_THRESHOLD` | Classifier probability that counts as PII (default `0.5`) |
| `JEV_GUARD_MAX_CHARS` | Max request size (default `100000`) |

## Data security

- **Local by default.** With no classifier URL nothing leaves the process. Using hosted Jev sends your text to a third party; choose that deliberately.
- Plaintext `http://` is refused for non-loopback classifier hosts unless explicitly allowed (private compose network).
- Fail closed: if the classifier is configured but unavailable, scans error (HTTP 502 / exit 2) instead of reporting "clean".
- Request bodies and matched values are never logged or included in findings or errors.
- Container: non-root, read-only filesystem, all capabilities dropped, API bound to `127.0.0.1`; the model container publishes no ports.
- Put a TLS-terminating proxy in front before exposing the API beyond localhost. See [SECURITY.md](SECURITY.md).
- Detection is probabilistic: don't treat a "clean" result as a guarantee.

## Development

```bash
uv sync
uv run pytest
uv run ruff check . && uv run ruff format --check .
```

`Dockerfile.kev` (local model) pins a Kev commit and has not been validated on GPU hosts; the classifier models are far larger than the guard image.

## Contributing & license

See [CONTRIBUTING.md](CONTRIBUTING.md). Licensed under [Apache-2.0](LICENSE).
