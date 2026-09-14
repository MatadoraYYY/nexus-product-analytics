import pandas as pd
from src.nexus.metrics.core import stickiness, ltv, ltv_cac

ACTIVE={"login","project_created","task_created","feature_used"}

def build_marts(users,events,payments,subscriptions,marketing,gross_margin=.8):
    a=events[events.event_name.isin(ACTIVE)]; daily=[]
    for d in pd.date_range(events.event_date.min(),events.event_date.max()).date:
        dau=a[a.event_date.eq(d)].user_id.nunique(); mau=a[a.event_date.between(d-pd.Timedelta(29,"d"),d)].user_id.nunique()
        daily.append({"date":d,"dau":dau,"wau":a[a.event_date.between(d-pd.Timedelta(6,"d"),d)].user_id.nunique(),"mau":mau,"stickiness":stickiness(dau,mau)})
    p=events[events.event_name.eq("project_created")].groupby("user_id").event_date.min().rename("project_date")
    t=events[events.event_name.eq("task_created")].groupby("user_id").event_date.min().rename("task_date")
    act=users[["user_id","registration_date"]].join(p,on="user_id").join(t,on="user_id")
    act["activated_flag"]=((act.project_date.between(act.registration_date,act.registration_date+pd.Timedelta(6,"d")))&(act.task_date.between(act.registration_date,act.registration_date+pd.Timedelta(6,"d")))).astype(int)
    signup=users.user_id.nunique(); activated=int(act.activated_flag.sum()); checkout=events[events.event_name.eq("checkout_started")].user_id.nunique(); paid=events[events.event_name.eq("subscription_started")].user_id.nunique()
    funnel=pd.DataFrame([["Signup",signup,1,0],["Activation",activated,activated/signup if signup else None,1-activated/signup if signup else None],["Checkout",checkout,checkout/activated if activated else None,1-checkout/activated if activated else None],["Paid",paid,paid/checkout if checkout else None,1-paid/checkout if checkout else None]],columns=["step","users","conversion_rate","drop_off"])
    c=users[["user_id","registration_date"]].merge(a[["user_id","event_date"]].drop_duplicates(),on="user_id"); c["age_day"]=(c.event_date-c.registration_date).dt.days
    ret=c[c.age_day.between(0,30)].groupby(["registration_date","age_day"]).user_id.nunique().reset_index(name="retained_users"); sizes=users.groupby("registration_date").user_id.nunique().reset_index(name="cohort_size"); ret=ret.merge(sizes,on="registration_date"); ret["retention_rate"]=ret.retained_users/ret.cohort_size
    pay=payments.copy(); pay["month"]=pd.to_datetime(pay.payment_date).dt.to_period("M").astype(str); rev=pay.groupby(["month","payment_type"]).amount.sum().unstack(fill_value=0).reset_index()
    for x in ["payment","refund","chargeback"]:
        if x not in rev: rev[x]=0.0
    rev["gross_revenue"]=rev.payment; rev["refunds"]=rev.refund; rev["chargebacks"]=rev.chargeback; rev["net_revenue"]=rev.gross_revenue-rev.refunds-rev.chargebacks
    sub=subscriptions.copy(); sub["start_month"]=pd.to_datetime(sub.start_date).dt.to_period("M").astype(str); sub["end_month"]=pd.to_datetime(sub.end_date).dt.to_period("M").astype("string")
    rev["mrr"]=rev.month.map(lambda m:sub.loc[(sub.start_month<=m)&(sub.end_month.isna()|sub.end_month.gt(m)),"monthly_price"].sum())
    econ=[]
    for m in rev.month:
        s=sub[(sub.start_month<=m)&(sub.end_month.isna()|sub.end_month.gt(m))]; revenue=float(rev.loc[rev.month.eq(m),"net_revenue"].iloc[0]); paying=s.user_id.nunique(); customers=users[users.registration_date.astype(str).str[:7]<=m].user_id.nunique()
        econ.append([m,customers,paying,revenue/customers if customers else None,revenue/paying if paying else None])
    economics=pd.DataFrame(econ,columns=["month","active_customers","paying_customers","arpu","arppu"]); economics["churn"]=None; economics["cac"]=None; economics["ltv"]=None; economics["ltv_cac"]=None
    feat=events[events.event_name.eq("feature_used")].groupby("feature_name").user_id.nunique().reset_index(name="users"); feat["adoption_rate"]=feat.users/signup; feat["d30_retention"]=None
    return {"daily":pd.DataFrame(daily),"activation":act,"funnel":funnel,"retention":ret,"revenue":rev,"economics":economics,"features":feat}
