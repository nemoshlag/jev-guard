# jev-guard

Local PII (Personally Identifiable Information) detection and guarding, powered by [jev](https://github.com/jev).

## Overview

`jev-guard` runs PII detection entirely on your local machine using `jev`, so sensitive data never has to leave your environment. It can be used to scan text, files, or data pipelines for PII before it's logged, stored, or transmitted elsewhere.

## Features

- Local-only PII detection — no external API calls or data egress
- Simple Python API for integrating PII checks into existing workflows
- Extensible detection rules

## Installation

This project uses [uv](https://github.com/astral-sh/uv) for dependency management.

```bash
uv sync
```

## Usage

```python
import jev_guard

# usage example coming soon
```

## Development

```bash
uv sync --extra dev
uv run pytest
```

## License

MIT

