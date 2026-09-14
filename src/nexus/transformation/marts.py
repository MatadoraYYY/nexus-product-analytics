import pandas as pd

from src.nexus.metrics.core import ltv, ltv_cac, stickiness


ACTIVE = {"login", "project_created", "task_created", "feature_used"}


def build_marts(users, events, payments, subscriptions, marketing, gross_margin=0.8):
    active_events = events[events.event_name.isin(ACTIVE)]
    daily = []
    for day in pd.date_range(events.event_date.min(), events.event_date.max()).date:
        dau = active_events[active_events.event_date.eq(day)].user_id.nunique()
        wau = active_events[active_events.event_date.between(day - pd.Timedelta(6, "d"), day)].user_id.nunique()
        mau = active_events[active_events.event_date.between(day - pd.Timedelta(29, "d"), day)].user_id.nunique()
        daily.append({"date": day, "dau": dau, "wau": wau, "mau": mau, "stickiness": stickiness(dau, mau)})

    first_project = events[events.event_name.eq("project_created")].groupby("user_id").event_date.min().rename("project_date")
    first_task = events[events.event_name.eq("task_created")].groupby("user_id").event_date.min().rename("task_date")
    activation = users[["user_id", "registration_date"]].join(first_project, on="user_id").join(first_task, on="user_id")
    activation["activated_flag"] = (
        activation.project_date.between(activation.registration_date, activation.registration_date + pd.Timedelta(6, "d"))
        & activation.task_date.between(activation.registration_date, activation.registration_date + pd.Timedelta(6, "d"))
    ).astype(int)

    signup = users.user_id.nunique()
    activated = int(activation.activated_flag.sum())
    checkout = events[events.event_name.eq("checkout_started")].user_id.nunique()
    paid = events[events.event_name.eq("subscription_started")].user_id.nunique()
    funnel = pd.DataFrame(
        [
            ["Signup", signup, 1, 0],
            ["Activation", activated, activated / signup if signup else None, 1 - activated / signup if signup else None],
            ["Checkout", checkout, checkout / activated if activated else None, 1 - checkout / activated if activated else None],
            ["Paid", paid, paid / checkout if checkout else None, 1 - paid / checkout if checkout else None],
        ],
        columns=["step", "users", "conversion_rate", "drop_off"],
    )

    cohort_events = users[["user_id", "registration_date"]].merge(
        active_events[["user_id", "event_date"]].drop_duplicates(), on="user_id"
    )
    cohort_events["age_day"] = (cohort_events.event_date - cohort_events.registration_date).dt.days
    retention = cohort_events[cohort_events.age_day.between(0, 30)].groupby(
        ["registration_date", "age_day"]
    ).user_id.nunique().reset_index(name="retained_users")
    cohort_sizes = users.groupby("registration_date").user_id.nunique().reset_index(name="cohort_size")
    retention = retention.merge(cohort_sizes, on="registration_date")
    retention["retention_rate"] = retention.retained_users / retention.cohort_size

    pay = payments.copy()
    pay["month"] = pd.to_datetime(pay.payment_date).dt.to_period("M").astype(str)
    rev = pay.groupby(["month", "payment_type"]).amount.sum().unstack(fill_value=0).reset_index()
    for payment_type in ["payment", "refund", "chargeback"]:
        if payment_type not in rev:
            rev[payment_type] = 0.0
    rev["gross_revenue"] = rev.payment
    rev["refunds"] = rev.refund
    rev["chargebacks"] = rev.chargeback
    rev["net_revenue"] = rev.gross_revenue - rev.refunds - rev.chargebacks

    sub = subscriptions.copy()
    sub["start_month"] = pd.to_datetime(sub.start_date).dt.to_period("M").astype(str)
    sub["end_month"] = pd.to_datetime(sub.end_date).dt.to_period("M").astype("string")
    rev["mrr"] = rev.month.map(
        lambda month: sub.loc[
            (sub.start_month <= month) & (sub.end_month.isna() | sub.end_month.gt(month)), "monthly_price"
        ].sum()
    )

    monthly_rows = []
    paying_by_month = {}
    start_by_month = sub.groupby("start_month").user_id.nunique().to_dict()
    spend_by_month = marketing.assign(month=pd.to_datetime(marketing.date).dt.to_period("M").astype(str)).groupby("month").spend.sum().to_dict()
    for month in rev.month:
        active_users = active_events.loc[
            active_events.event_date.astype(str).str[:7].eq(month), "user_id"
        ].nunique()
        current_paying = sub.loc[
            (sub.start_month <= month) & (sub.end_month.isna() | sub.end_month.gt(month)), "user_id"
        ].nunique()
        previous_month = str(pd.Period(month) - 1)
        previous_paying = paying_by_month.get(previous_month)
        churn = (
            max(previous_paying - current_paying, 0) / previous_paying
            if previous_paying
            else None
        )
        revenue = float(rev.loc[rev.month.eq(month), "net_revenue"].iloc[0])
        arpu = revenue / active_users if active_users else None
        arppu = revenue / current_paying if current_paying else None
        cac = spend_by_month.get(month, 0) / start_by_month.get(month, 0) if start_by_month.get(month, 0) else None
        customer_ltv = ltv(arpu, gross_margin, churn)
        monthly_rows.append([month, active_users, current_paying, arpu, arppu, churn, cac, customer_ltv, ltv_cac(customer_ltv, cac)])
        paying_by_month[month] = current_paying

    economics = pd.DataFrame(
        monthly_rows,
        columns=["month", "active_customers", "paying_customers", "arpu", "arppu", "churn", "cac", "ltv", "ltv_cac"],
    )

    feature_users = events[events.event_name.eq("feature_used")][["feature_name", "user_id", "event_date"]].drop_duplicates()
    features = feature_users.groupby("feature_name").user_id.nunique().reset_index(name="users")
    features["adoption_rate"] = features.users / signup
    d30 = []
    for feature in features.feature_name:
        first = feature_users[feature_users.feature_name.eq(feature)].groupby("user_id").event_date.min().rename("first_feature_date")
        eligible = users[["user_id"]].merge(first, on="user_id").dropna()
        retained = active_events.merge(eligible, on="user_id")
        retained = retained[(retained.event_date - retained.first_feature_date).dt.days.ge(30)]
        d30.append(retained.user_id.nunique() / eligible.user_id.nunique() if len(eligible) else None)
    features["d30_retention"] = d30

    return {
        "daily": pd.DataFrame(daily),
        "activation": activation,
        "funnel": funnel,
        "retention": retention,
        "revenue": rev,
        "economics": economics,
        "features": features,
    }
