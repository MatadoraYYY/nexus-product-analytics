# Changelog

## Unreleased
- Added a versioned metric contract and golden-value tests for core KPI semantics.
- Enforced the DAU ≤ MAU invariant in the stickiness metric.
- Added reproducible Ruff/Pytest project configuration and CI lint/test execution.
- Documented the free-budget deployment model, synthetic-data limitations and operating architecture.
- Made Render health checks non-blocking while synthetic analytics data is generated in the background.
- Completed monthly churn, CAC, LTV, LTV:CAC, and feature D30 retention marts.
- Made the acquisition funnel sequential by emitting checkout events for subscription starts.
- Expanded the dashboard with funnel, revenue, and feature-adoption views.

## 1.0.0
- Initial NEXUS Product Analytics platform.
