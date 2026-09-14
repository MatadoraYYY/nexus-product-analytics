from __future__ import annotations

from math import sqrt
from statistics import NormalDist


def safe_divide(a: float, b: float) -> float | None:
    return None if b == 0 else a / b


def activation_rate(activated_users: int, registered_users: int) -> float | None:
    if min(activated_users, registered_users) < 0:
        raise ValueError("Counts must be non-negative")
    if activated_users > registered_users:
        raise ValueError("Activated users cannot exceed registered users")
    return safe_divide(activated_users, registered_users)


def stickiness(dau: int, mau: int) -> float | None:
    if min(dau, mau) < 0:
        raise ValueError("Counts must be non-negative")
    if dau > mau:
        raise ValueError("DAU cannot exceed MAU")
    return safe_divide(dau, mau)


def conversion_rate(next_users: int, previous_users: int) -> float | None:
    if min(next_users, previous_users) < 0:
        raise ValueError("Counts must be non-negative")
    if next_users > previous_users:
        raise ValueError("Next step cannot exceed previous step")
    return safe_divide(next_users, previous_users)


def drop_off(next_users: int, previous_users: int) -> float | None:
    c = conversion_rate(next_users, previous_users)
    return None if c is None else 1 - c


def ltv(arpu: float | None, gross_margin: float, monthly_churn: float | None) -> float | None:
    if arpu is None or monthly_churn is None:
        return None
    if arpu < 0 or not 0 <= gross_margin <= 1 or monthly_churn < 0:
        raise ValueError("Invalid LTV inputs")
    return None if monthly_churn == 0 else arpu * gross_margin / monthly_churn


def ltv_cac(ltv_value: float | None, cac: float | None) -> float | None:
    return None if ltv_value is None or cac in (None, 0) else ltv_value / cac


def ab_test(control_conversions: int, control_n: int, treatment_conversions: int, treatment_n: int, alpha=0.05):
    if min(control_conversions, control_n, treatment_conversions, treatment_n) < 0:
        raise ValueError("Counts must be non-negative")
    if control_conversions > control_n or treatment_conversions > treatment_n:
        raise ValueError("Conversions cannot exceed sample size")
    if control_n == 0 or treatment_n == 0:
        raise ValueError("Sample sizes must be positive")
    p1, p2 = control_conversions / control_n, treatment_conversions / treatment_n
    pooled = (control_conversions + treatment_conversions) / (control_n + treatment_n)
    se = sqrt(pooled * (1 - pooled) * (1 / control_n + 1 / treatment_n))
    z = 0 if se == 0 else (p2 - p1) / se
    p = 2 * (1 - NormalDist().cdf(abs(z))) if se else 1.0
    se_diff = sqrt(p1 * (1 - p1) / control_n + p2 * (1 - p2) / treatment_n)
    zcrit = NormalDist().inv_cdf(1 - alpha / 2)
    diff = p2 - p1
    return {
        "control_n": control_n,
        "treatment_n": treatment_n,
        "control_conversions": control_conversions,
        "treatment_conversions": treatment_conversions,
        "control_rate": p1,
        "treatment_rate": p2,
        "absolute_diff": diff,
        "relative_uplift": None if p1 == 0 else diff / p1,
        "p_value": p,
        "ci_low": diff - zcrit * se_diff,
        "ci_high": diff + zcrit * se_diff,
        "decision": "Reject H0" if p < alpha else "Do not reject H0",
        "warning": "Synthetic experiment; association does not establish causality.",
    }
