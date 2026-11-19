"""Generates structured assessment reports (used by Web Download & API)."""

from __future__ import annotations

from typing import Any
from .models import LoanApplication


class ReportGenerator:
    def generate_report(
        self,
        application: LoanApplication,
        prediction: dict[str, Any],
        financials: dict[str, Any],
        recommendation: str,
    ) -> dict[str, Any]:
        return {
            "application_id": application.application_id,
            "created_at": application.created_at,
            "applicant": application.applicant.to_dict(),
            "employment_profile": application.applicant.employment_profile(),
            "loan": {
                "amount": application.loan_amount,
                "term_months": application.loan_term_months,
            },
            "financial_metrics": financials,
            "ml_assessment": prediction,
            "recommendation": recommendation,
        }
