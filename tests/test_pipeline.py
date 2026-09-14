from src.nexus.ingestion.generator import GeneratorConfig,generate_users,generate_events,generate_financials
from src.nexus.validation.checks import validate,assert_valid

def test_generator_reproducible():
    cfg=GeneratorConfig(seed=42,users=100);u1=generate_users(cfg);e1=generate_events(u1,cfg);u2=generate_users(cfg);e2=generate_events(u2,cfg)
    assert u1.equals(u2);assert e1.drop(columns=['session_id']).equals(e2.drop(columns=['session_id']))

def test_contracts():
    cfg=GeneratorConfig(seed=42,users=100);u=generate_users(cfg);e=generate_events(u,cfg);s,p,m=generate_financials(u,e,cfg);assert_valid(validate(u,e,p,s,m))
