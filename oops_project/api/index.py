"""api/index.py — FastAPI serverless entrypoint for Vercel."""

from __future__ import annotations

from pathlib import Path
import sys

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

# Ensure oops_project root modules (core_oops, nakul_ml, kashjot_financials) are importable
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from core_oops import CreditRiskSystem, RiskAnalyzer
from nakul_ml import predict_application


app = FastAPI(title="Credit Risk Assessment API", version="1.0.0")
system = CreditRiskSystem(RiskAnalyzer(predict_application))


class ApplicationPayload(BaseModel):
    full_name: str
    age: int
    annual_income: float
    employment_type: str
    loan_amount: float
    loan_term_months: int
    credit_score: int
    existing_debt: float
    dependents: int


@app.get("/", response_class=HTMLResponse)
def serve_home() -> str:
    """Fallback route when running locally via uvicorn."""
    return (ROOT_DIR / "public" / "index.html").read_text(encoding="utf-8")


@app.get("/api/health")
def health_check() -> dict:
    return {"status": "ok", "service": "Credit Risk Assessment API"}


@app.post("/api/assess")
def assess_loan(payload: ApplicationPayload) -> dict:
    try:
        return system.assess_from_dict(payload.model_dump())
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err)) from err
