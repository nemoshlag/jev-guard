# Security Policy

## Reporting a vulnerability

Please report vulnerabilities privately via GitHub's
[private vulnerability reporting](https://github.com/nemoshlag/jev-guard/security/advisories/new).
Do not open public issues for security problems, and never include real PII in reports.

## Scope and guarantees

- jev-guard is a detection aid, not a guarantee. False negatives are possible.
- Text sent to a remote classifier leaves your environment; use a local model for sensitive data.
- Do not expose the API without TLS and an API key.
