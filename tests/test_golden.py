import json
from pathlib import Path

from src.nexus.metrics.core import activation_rate, drop_off, ltv, ltv_cac, stickiness


GOLDEN = json.loads((Path(__file__).parent / "fixtures" / "golden.json").read_text())


def test_metric_golden_values():
    values = {
        "activation_rate": activation_rate(40, 100),
        "stickiness": stickiness(20, 50),
        "drop_off": drop_off(400, 1000),
        "ltv": ltv(30, 0.8, 0.05),
        "ltv_cac": ltv_cac(480, 100),
    }
    assert values == GOLDEN
