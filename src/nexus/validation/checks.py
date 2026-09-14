from __future__ import annotations

import pandas as pd

ALLOWED_EVENTS = {
    "signup",
    "login",
    "project_created",
    "task_created",
    "team_invited",
    "feature_used",
    "checkout_started",
    "subscription_started",
    "subscription_cancelled",
}
ALLOWED_FEATURES = {"kanban", "calendar", "automation", "reports", "integrations", "ai_assistant"}
ALLOWED_DEVICES = {"web", "ios", "android"}
ALLOWED_CHANNELS = {"organic", "paid_search", "paid_social", "referral", "partner", "content"}


def validate(users, events, payments, subscriptions, marketing) -> dict[str, int]:
    return {
        "pk_users": int(users.user_id.duplicated().sum()),
        "pk_events": int(events.session_id.duplicated().sum()),
        "fk_events": int((~events.user_id.isin(users.user_id)).sum()),
        "fk_payments": int((~payments.user_id.isin(users.user_id)).sum()),
        "fk_subscriptions": int((~subscriptions.user_id.isin(users.user_id)).sum()),
        "invalid_events": int((~events.event_name.isin(ALLOWED_EVENTS)).sum()),
        "invalid_features": int((events.feature_name.notna() & ~events.feature_name.isin(ALLOWED_FEATURES)).sum()),
        "invalid_devices": int((~users.device.isin(ALLOWED_DEVICES)).sum()),
        "invalid_channels": int((~users.acquisition_channel.isin(ALLOWED_CHANNELS)).sum()),
        "negative_amounts": int((payments.amount < 0).sum()),
        "null_users": int(users.isna().any(axis=1).sum()),
        "future_events": int((events.event_date > pd.Timestamp("2026-06-30").date()).sum()),
    }


def assert_valid(checks: dict[str, int]) -> None:
    failures = {k: v for k, v in checks.items() if v}
    if failures:
        raise ValueError(f"Data quality checks failed: {failures}")
