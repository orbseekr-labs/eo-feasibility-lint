# Security Policy

## Supported versions

| Version | Supported |
| --- | --- |
| 0.1.x | yes |

## Reporting a vulnerability

Please report security issues privately through [GitHub's private vulnerability reporting](https://github.com/orbseekr-labs/eo-feasibility-lint/security/advisories/new) rather than a public issue.

Include what you did, what happened, and what you expected. We aim to acknowledge a report within a week.

Please do not include real credentials or third-party data in a report.

## Threat model

`eo-feasibility-lint` is an offline command-line tool. It reads a requirement file you point it at and writes a report to stdout. It has no server, no daemon, no account and no persistent state.

The main untrusted input is the **requirement document**, which may come from a third party or an automated pipeline. The properties below are the ones we treat as security-relevant, and each is covered by tests.

### Guarantees

- **Safe parsing.** YAML is read with a `yaml.SafeLoader` subclass only. Arbitrary Python object construction (`!!python/object/apply:...`) is rejected as a parse error, never executed. JSON input is read with the standard library `json` module.
- **No ambiguous documents.** Duplicate mapping keys are rejected in both YAML and JSON rather than silently resolved last-value-wins, so a document's meaning never depends on parser behaviour.
- **No code execution from input.** No `eval`, no `exec`, no template rendering, no shell invocation derived from a requirement document.
- **No network access.** The runtime makes no network requests under any circumstance. Source URLs in the catalog are provenance metadata and are never fetched. The tool imports no HTTP client.
- **No telemetry, analytics or uploads.** Requirement files never leave the machine.
- **No credentials.** The tool reads no API keys, tokens or configuration outside the file you pass it.
- **No environment leakage in reports.** JSON output contains no timestamp, hostname, username, filesystem path or random identifier. It is byte-identical across runs and machines.
- **Bounded runtime dependencies.** PyYAML is the only runtime dependency. Adding another requires a specification change.

### Not covered

- The catalog describes public satellite mission capabilities. It is not sensitive data and is not authenticated beyond its cited first-party sources.
- Verdicts are engineering judgements about documented capabilities, not safety guarantees. `PASS` never means a real EO project will succeed. See the README.
- Resource exhaustion from a pathologically large input file is not treated as a vulnerability; the tool reads what you give it.

## Dependency and supply chain

- GitHub Actions in CI are pinned to immutable commit SHAs.
- CI runs `ruff check .` and `pytest` on Python 3.11, 3.12 and 3.13, plus an installed-CLI smoke test.
- No secrets are used by CI, and the workflow requests read-only permissions.
