from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
import json
import uuid

import numpy as np
import pandas as pd

EVENTS = ["signup","login","project_created","task_created","team_invited",
          "feature_used","checkout_started","subscription_started","subscription_cancelled"]
FEATURES = ["kanban","calendar","automation","reports","integrations","ai_assistant"]
CHANNELS = ["organic","paid_search","paid_social","referral","partner","content"]
DEVICES = ["web","ios","android"]
COUNTRIES = ["Poland","Russia","Germany","UK","US","other_synthetic"]
PLANS = ["free","pro","team"]

@dataclass(frozen=True)
class GeneratorConfig:
    seed: int = 42
    users: int = 50_000
    start_date: date = date(2026,1,1)
    end_date: date = date(2026,6,30)

def _uids(n: int, rng: np.random.Generator) -> list[str]:
    return [str(uuid.UUID(int=(int(rng.integers(0, 2**64, dtype=np.uint64)) << 64) | int(rng.integers(0, 2**64, dtype=np.uint64)))) for _ in range(n)]

def generate_users(cfg: GeneratorConfig) -> pd.DataFrame:
    rng = np.random.default_rng(cfg.seed)
    n = cfg.users
    days = (cfg.end_date - cfg.start_date).days + 1
    registration_date = [cfg.start_date + timedelta(days=int(x)) for x in rng.integers(0, days, n)]
    ts = [f"{d.isoformat()}T{int(rng.integers(0,86400))//3600:02d}:{int(rng.integers(0,3600))//60:02d}:00" for d in registration_date]
    return pd.DataFrame({
        "user_id": _uids(n, rng),
        "registration_timestamp": pd.to_datetime(ts, utc=True),
        "registration_date": registration_date,
        "country": rng.choice(COUNTRIES, n, p=[.25,.20,.15,.10,.10,.20]),
        "device": rng.choice(DEVICES, n, p=[.55,.25,.20]),
        "acquisition_channel": rng.choice(CHANNELS, n, p=[.30,.20,.15,.15,.10,.10]),
        "plan_at_signup": rng.choice(PLANS, n, p=[.75,.20,.05]),
        "dataset_version": "1.0.0",
    })

def generate_events(users: pd.DataFrame, cfg: GeneratorConfig) -> pd.DataFrame:
    rng = np.random.default_rng(cfg.seed + 1)
    rows = []
    feature_probs = {"kanban":.35,"calendar":.25,"automation":.18,"reports":.15,"integrations":.10,"ai_assistant":.08}
    for r in users.itertuples(index=False):
        reg = r.registration_date
        horizon = min((cfg.end_date - reg).days, 30)
        active_days = rng.binomial(max(horizon, 0), .28)
        chosen = rng.choice(np.arange(horizon + 1), size=min(active_days, horizon + 1), replace=False) if horizon >= 0 else []
        rows.append((r.user_id, reg, "signup", None))
        has_project = False
        has_task = False
        for age in sorted(chosen):
            d = reg + timedelta(days=int(age))
            if rng.random() < .65:
                rows.append((r.user_id,d,"login",None))
            if rng.random() < (.18 if r.plan_at_signup == "free" else .30):
                has_project = True
                rows.append((r.user_id,d,"project_created",None))
            if has_project and rng.random() < .55:
                has_task = True
                rows.append((r.user_id,d,"task_created",None))
            if has_project and has_task and rng.random() < .75:
                feat = rng.choice(list(feature_probs), p=np.array(list(feature_probs.values()))/sum(feature_probs.values()))
                rows.append((r.user_id,d,"feature_used",str(feat)))
            if r.plan_at_signup in ("pro","team") and rng.random() < .12:
                rows.append((r.user_id,d,"team_invited",None))
        if r.plan_at_signup == "free" and rng.random() < .10:
            rows.append((r.user_id, min(reg + timedelta(days=7), cfg.end_date), "checkout_started", None))
        if r.plan_at_signup in ("pro","team") or rng.random() < .04:
            subday = min(reg + timedelta(days=int(rng.integers(0,15))), cfg.end_date)
            rows.append((r.user_id, subday, "subscription_started", None))
    df = pd.DataFrame(rows, columns=["user_id","event_date","event_name","feature_name"])
    df["event_timestamp"] = pd.to_datetime(df["event_date"].astype(str) + "T12:00:00", utc=True)
    df["session_id"] = [str(uuid.uuid4()) for _ in range(len(df))]
    df["platform"] = "web"
    df["properties_json"] = df["feature_name"].map(lambda x: json.dumps({"feature": x}) if pd.notna(x) else "{}")
    return df[["event_date","event_timestamp","user_id","event_name","session_id","platform","feature_name","properties_json"]]

def generate_financials(users: pd.DataFrame, events: pd.DataFrame, cfg: GeneratorConfig):
    rng = np.random.default_rng(cfg.seed + 2)
    starts = events.loc[events.event_name=="subscription_started", ["user_id","event_date"]].drop_duplicates()
    subs = []
    pays = []
    prices = {"free":0.0,"pro":49.0,"team":129.0}
    for r in starts.itertuples(index=False):
        plan = users.loc[users.user_id.eq(r.user_id), "plan_at_signup"].iloc[0]
        start = r.event_date
        end = None if rng.random() < .82 else min(start + timedelta(days=int(rng.integers(30,120))), cfg.end_date)
        subs.append((str(uuid.uuid4()), r.user_id, start, end, plan, prices[plan], "active" if end is None else "cancelled"))
        months = pd.date_range(start=start, end=cfg.end_date, freq="MS")
        for m in months:
            pays.append((str(uuid.uuid4()), r.user_id, pd.Timestamp(m).date(), prices[plan], "USD","payment","succeeded","1.0.0"))
    payments = pd.DataFrame(pays, columns=["payment_id","user_id","payment_date","amount","currency","payment_type","payment_status","dataset_version"])
    subscriptions = pd.DataFrame(subs, columns=["subscription_id","user_id","start_date","end_date","plan","monthly_price","status"])
    if not payments.empty:
        refund_n = max(1, int(len(payments)*.02))
        for idx in rng.choice(len(payments), refund_n, replace=False):
            base = payments.iloc[idx]
            payments.loc[len(payments)] = [str(uuid.uuid4()),base.user_id,base.payment_date,round(base.amount*.5,2),"USD","refund","succeeded","1.0.0"]
        cb_n = max(1, int(len(payments)*.003))
        for idx in rng.choice(len(payments), cb_n, replace=False):
            base = payments.iloc[idx]
            payments.loc[len(payments)] = [str(uuid.uuid4()),base.user_id,base.payment_date,round(base.amount*.5,2),"USD","chargeback","succeeded","1.0.0"]
    marketing = []
    for d in pd.date_range(cfg.start_date,cfg.end_date):
        for ch in CHANNELS:
            marketing.append((d.date(), ch, round(float(rng.gamma(2.0, 35.0)),2),"USD","1.0.0"))
    marketing_costs = pd.DataFrame(marketing, columns=["date","channel","spend","currency","dataset_version"])
    return subscriptions, payments, marketing_costs
