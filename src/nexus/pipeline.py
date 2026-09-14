from pathlib import Path
from src.nexus.config.settings import Settings
from src.nexus.ingestion.generator import GeneratorConfig,generate_users,generate_events,generate_financials
from src.nexus.validation.checks import validate,assert_valid
from src.nexus.transformation.marts import build_marts

def run():
    s=Settings(); Path(s.data_dir).mkdir(exist_ok=True); cfg=GeneratorConfig(seed=s.seed)
    users=generate_users(cfg); events=generate_events(users,cfg); subscriptions,payments,marketing=generate_financials(users,events,cfg)
    checks=validate(users,events,payments,subscriptions,marketing); assert_valid(checks)
    marts=build_marts(users,events,payments,subscriptions,marketing,s.gross_margin)
    db=__import__("duckdb"); con=db.connect(s.duckdb_path)
    tables={"dim_users":users,"fact_events":events,"fact_payments":payments,"fact_subscriptions":subscriptions,"marketing_costs":marketing,"mart_daily_kpis":marts["daily"],"mart_activation":marts["activation"],"mart_funnel":marts["funnel"],"mart_retention":marts["retention"],"mart_revenue_monthly":marts["revenue"],"mart_customer_economics":marts["economics"],"mart_feature_usage":marts["features"]}
    for name,df in tables.items():
        con.register(name+"_df",df); con.execute(f"CREATE OR REPLACE TABLE {name} AS SELECT * FROM {name}_df")
    con.close(); return checks

if __name__=="__main__": print(run())
