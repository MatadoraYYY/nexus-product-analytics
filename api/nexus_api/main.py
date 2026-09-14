import os
import threading
import uuid
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.nexus.pipeline import run


db_path = os.getenv("DUCKDB_PATH", "data/nexus.duckdb")
app = FastAPI(title="NEXUS Product Intelligence API", version="1.0.0")
origins = [x.strip() for x in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",") if x.strip()]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_methods=["GET"], allow_headers=["*"])

_pipeline_state = {"status": "ready" if Path(db_path).exists() else "building", "error": None}


def _build_pipeline():
    try:
        run()
        _pipeline_state["status"] = "ready"
    except Exception as exc:
        _pipeline_state["status"] = "error"
        _pipeline_state["error"] = str(exc)


@app.on_event("startup")
def startup_pipeline():
    if not Path(db_path).exists():
        threading.Thread(target=_build_pipeline, daemon=True).start()


@app.middleware("http")
async def request_id(request: Request, call_next):
    rid = str(uuid.uuid4())
    request.state.request_id = rid
    response = await call_next(request)
    response.headers["X-Request-ID"] = rid
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


def q(sql, params=None):
    db = __import__("duckdb")
    con = db.connect(db_path, read_only=True)
    try:
        return con.execute(sql, params or []).df()
    finally:
        con.close()


@app.get("/health")
def health():
    return {"status": "ok", "pipeline": _pipeline_state["status"]}


def _require_ready():
    if _pipeline_state["status"] != "ready" or not Path(db_path).exists():
        return JSONResponse(
            status_code=503,
            content={
                "error": {
                    "code": "ANALYTICS_NOT_READY",
                    "message": "Analytics dataset is still being prepared.",
                }
            },
        )
    return None


@app.get("/api/v1/overview")
def overview():
    not_ready = _require_ready()
    if not_ready:
        return not_ready
    d = q("SELECT * FROM mart_daily_kpis ORDER BY date DESC LIMIT 1").iloc[0]
    r = q("SELECT * FROM mart_revenue_monthly ORDER BY month DESC LIMIT 1").iloc[0]
    e = q("SELECT * FROM mart_customer_economics ORDER BY month DESC LIMIT 1").iloc[0]
    a = float(q("SELECT AVG(activated_flag) rate FROM mart_activation").iloc[0]["rate"])
    d30 = q("SELECT AVG(retention_rate) rate FROM mart_retention WHERE age_day=30").iloc[0]["rate"]
    return {
        "period": str(r["month"]),
        "dau": int(d.dau),
        "mau": int(d.mau),
        "stickiness": d.stickiness,
        "activation_rate": a,
        "d30_retention": d30,
        "mrr": float(r.mrr),
        "churn": e.churn,
        "arpu": e.arpu,
        "arppu": e.arppu,
        "ltv": e.ltv,
        "cac": e.cac,
        "ltv_cac": e.ltv_cac,
    }


@app.get("/api/v1/funnel")
def funnel():
    not_ready = _require_ready()
    return not_ready or q("SELECT * FROM mart_funnel").to_dict("records")


@app.get("/api/v1/retention")
def retention():
    not_ready = _require_ready()
    return not_ready or q("SELECT * FROM mart_retention ORDER BY registration_date, age_day").to_dict("records")


@app.get("/api/v1/revenue")
def revenue():
    not_ready = _require_ready()
    return not_ready or q("SELECT * FROM mart_revenue_monthly ORDER BY month").to_dict("records")


@app.get("/api/v1/features")
def features():
    not_ready = _require_ready()
    return not_ready or q("SELECT * FROM mart_feature_usage ORDER BY adoption_rate DESC").to_dict("records")


@app.get("/api/v1/cohorts")
def cohorts():
    not_ready = _require_ready()
    return not_ready or q("SELECT * FROM mart_retention ORDER BY registration_date, age_day").to_dict("records")


@app.exception_handler(Exception)
async def safe_error(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "Internal server error",
                "request_id": getattr(request.state, "request_id", "unknown"),
            }
        },
    )
