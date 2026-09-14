from __future__ import annotations

import json
from pathlib import Path

from src.nexus.metrics.core import activation_rate, ltv, ltv_cac, stickiness

GOLDEN_PATH = Path(__file__).parent / "fixtures" / "golden_metrics.json"


def test_metric_golden_values():
    golden = json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))
    assert activation_rate(**golden["activation_rate"]["input"]) == golden["activation_rate"]["expected"]
    assert stickiness(**golden["stickiness"]["input"]) == golden["stickiness"]["expected"]
    assert ltv(**golden["ltv"]["input"]) == golden["ltv"]["expected"]
    assert ltv_cac(480, 80) == golden["ltv_cac"]["expected"]
