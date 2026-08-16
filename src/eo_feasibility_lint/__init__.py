"""eo-feasibility-lint: a deterministic, offline Earth observation feasibility linter.

The runtime makes no network requests, uses no LLM, collects no telemetry and
reads no API keys. The same input plus the same catalog and ruleset versions
always produces the same result.
"""

from .models import RULESET_VERSION, SCHEMA_VERSION

__version__ = RULESET_VERSION

__all__ = ["RULESET_VERSION", "SCHEMA_VERSION", "__version__"]
