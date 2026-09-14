# NEXUS metric contract

The frontend is presentation-only. KPI definitions live in `src/nexus/metrics/core.py` and the marts layer.

| Metric | Definition | Edge case |
|---|---|---|
| Activation | Users with both first project and first task within 7 days / registered users | `None` if denominator is zero |
| DAU | Distinct users with an active event on a day | — |
| MAU | Distinct users with an active event in the trailing 30-day window | — |
| Stickiness | DAU / MAU | DAU > MAU is invalid |
| D30 retention | Registered cohort users active on age day 30 / cohort size | Missing cohort activity is not imputed as a positive observation |
| MRR | Monthly recurring subscription value for subscriptions active in the month | Subscription ending in the month is excluded after its end date |
| CAC | Marketing spend / new subscription starters in month | `None` when there are no new starters |
| LTV | ARPU × gross margin / monthly churn | `None` when churn is zero |
| LTV:CAC | LTV / CAC | `None` when CAC is zero or unavailable |

Metric changes must update tests and `CHANGELOG.md` in the same change set.
