# Changelog

All notable changes are documented here. Format based on [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

## [0.1.0] - 2026-10-09

### Added
- Regex PII detection via Presidio pattern recognizers (email, credit card, SSN, phone, IP, IBAN).
- System One (Jev/Kev) `noul` classifier client with local or remote endpoint.
- FastAPI service (`/v1/scan`, `/healthz`) with bearer auth, size limit, fail-closed errors.
- CLI (`scan`, `serve`), hardened Docker Compose stack with optional local Kev profile.
- End-to-end demo, CI with coverage gate and `pip-audit`.
