import pytest

from src.nexus.metrics.core import activation_rate, ab_test, drop_off, ltv, ltv_cac, stickiness


def test_activation():
    assert activation_rate(40, 100) == 0.4


def test_stickiness():
    assert stickiness(20, 50) == 0.4


def test_stickiness_rejects_invalid_ratio():
    with pytest.raises(ValueError):
        stickiness(51, 50)


def test_dropoff():
    assert drop_off(400, 1000) == 0.6


def test_ltv_zero_churn():
    assert ltv(30, 0.8, 0) is None


def test_ltv():
    assert ltv(30, 0.8, 0.05) == 480


def test_ltv_cac_zero():
    assert ltv_cac(480, 0) is None


def test_ab():
    assert ab_test(10, 100, 20, 100)["treatment_rate"] == 0.2
