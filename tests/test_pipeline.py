from src.nexus.ingestion.generator import GeneratorConfig, generate_events, generate_financials, generate_users
from src.nexus.transformation.marts import build_marts
from src.nexus.validation.checks import assert_valid, validate


def test_generator_reproducible():
    cfg = GeneratorConfig(seed=42, users=100)
    u1 = generate_users(cfg)
    e1 = generate_events(u1, cfg)
    u2 = generate_users(cfg)
    e2 = generate_events(u2, cfg)
    assert u1.equals(u2)
    assert e1.drop(columns=["session_id"]).equals(e2.drop(columns=["session_id"]))


def test_contracts():
    cfg = GeneratorConfig(seed=42, users=100)
    users = generate_users(cfg)
    events = generate_events(users, cfg)
    subscriptions, payments, marketing = generate_financials(users, events, cfg)
    assert_valid(validate(users, events, payments, subscriptions, marketing))


def test_marts_have_customer_economics_and_sequential_funnel():
    cfg = GeneratorConfig(seed=42, users=100)
    users = generate_users(cfg)
    events = generate_events(users, cfg)
    subscriptions, payments, marketing = generate_financials(users, events, cfg)
    marts = build_marts(users, events, payments, subscriptions, marketing)
    funnel = marts["funnel"]
    assert (funnel["conversion_rate"].dropna() <= 1).all()
    assert marts["economics"]["cac"].notna().any()
    assert marts["economics"]["ltv"].notna().any()
