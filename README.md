# NEXUS — Product Analytics

End-to-end portfolio product analytics platform: synthetic event generation → data-quality gates → DuckDB marts → backend metric layer → versioned FastAPI → React dashboard → CI/CD → Render.

## What this demonstrates

- Product funnel: Signup → Activation → Checkout → Paid
- Activation, DAU/MAU, stickiness and D30 retention
- Revenue, refunds, chargebacks and MRR
- Customer economics: ARPU, ARPPU, churn, CAC, LTV and LTV:CAC
- Feature adoption and retention by feature
- Statistical A/B-test helper with confidence interval and synthetic-data warning
- Critical DQ checks that fail the pipeline on invalid data
- Metric contract + golden tests so semantic changes are explicit
- Frontend contains presentation logic only; KPI calculations stay in Python/domain/marts

## Architecture

```text
Synthetic generator
       ↓
Validation / DQ gate
       ↓
Pandas transformations → DuckDB marts
       ↓
Domain metric layer
       ↓
FastAPI /api/v1/*
       ↓
React + Plotly dashboard
```

The demo intentionally uses DuckDB on the Render Free filesystem. Render Free storage is ephemeral, so the dataset is rebuilt automatically when the service starts without an existing database.

## Local run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m src.nexus.pipeline
uvicorn api.nexus_api.main:app --reload
```

Dashboard:

```bash
cd frontend
npm install
npm run dev
```

## Tests

```bash
ruff check src api tests --ignore F401,E501
pytest -q
```

GitHub Actions runs both the test suite and the analytics pipeline on every relevant change.

## Demo

- API: https://nexus-product-analytics-api.onrender.com
- Dashboard: https://nexus-product-analytics-dashboard.onrender.com
- API health: https://nexus-product-analytics-api.onrender.com/health
- API docs: https://nexus-product-analytics-api.onrender.com/docs

## Free-budget design

No paid database, Redis, Kafka or Airflow is required. Render web services and the dashboard use the Free plan; analytics data is generated locally inside the service and is not treated as durable production storage.

## Important limitations

This is a portfolio/demo system using synthetic data. It is not a production persistence architecture. The A/B-test helper is statistical demonstration only and does not establish causality. Frontend production builds currently emit a large Plotly bundle; code splitting is a future optimization.

## Metric governance

See `docs/metric_contract.md`. When a metric definition changes, update the contract, golden tests and `CHANGELOG.md` together.
