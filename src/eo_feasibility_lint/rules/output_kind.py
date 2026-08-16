"""EFL801 / EFL802 / EFL803 - what the requested output implies.

These findings do not depend on any mission capability, so they carry no
source_ids. A business metric is never marked FAIL: an inference chain may still
be possible, it just cannot be judged from mission specifications.
"""

from __future__ import annotations

from ..catalog import Mission
from ..loader import Requirement
from ..models import CONDITIONAL, Finding

_FINDINGS = {
    "derived_product": (
        "EFL801",
        "Derived processing required",
        "The requested output is a derived product: processing beyond raw acquisition "
        "is required, and the mission specification alone cannot establish that it "
        "will succeed.",
    ),
    "model_inference": (
        "EFL802",
        "Model validation required",
        "A model is required to produce the requested output. Mission specifications "
        "alone cannot validate that model.",
    ),
    "business_metric": (
        "EFL803",
        "Business metric inference required",
        "The requested output is not directly observable from satellite mission "
        "specifications and requires an external inference chain and potentially "
        "non-EO data.",
    ),
}


def evaluate(requirement: Requirement, mission: Mission) -> list[Finding]:
    entry = _FINDINGS.get(requirement.output_kind)
    if entry is None:
        return []
    code, title, message = entry
    return [
        Finding(
            code=code,
            effect=CONDITIONAL,
            title=title,
            message=message,
            required={"output_kind": requirement.output_kind},
            capability={},
            source_ids=(),
        )
    ]
