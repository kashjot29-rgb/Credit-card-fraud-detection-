"""Rule-based recommendation generator."""

from __future__ import annotations

from typing import Any
from .models import LoanApplication


class DecisionAdvisor:
    """Produces actionable next steps from the ML risk level and applicant profile."""

    def generate_recommendation(
        self,
        application: LoanApplication,
        prediction: dict[str, Any],
    ) -> str:
        level = str(prediction.get("risk_level", "")).strip().title()
        profile = application.applicant.employment_profile()

        messages = {
            "Low": "Low risk estimated. Proceed with standard KYC and document verification.",
            "Medium": "Medium risk estimated. Verify income proofs and repayment capacity.",
            "High": "High risk estimated. Flag for manual underwriting review before any decision.",
        }
        if level not in messages:
            raise ValueError("Invalid risk_level for recommendation.")
        return f"{messages[level]} Profile: {profile}."
