"""Facade coordinating Core OOP models, ML predictor, and Financial Policy Engine."""

from __future__ import annotations

from typing import Any

from kashjot_financials import LoanPolicyEngine
from .decision_advisor import DecisionAdvisor
from .models import LoanApplication
from .report_generator import ReportGenerator
from .risk_analyzer import RiskAnalyzer


class CreditRiskSystem:
    def __init__(
        self,
        risk_analyzer: RiskAnalyzer,
        advisor: DecisionAdvisor | None = None,
        report_generator: ReportGenerator | None = None,
        policy_engine: LoanPolicyEngine | None = None,
    ) -> None:
        self.__risk_analyzer = risk_analyzer
        self.__advisor = advisor or DecisionAdvisor()
        self.__report_generator = report_generator or ReportGenerator()
        self.__policy_engine = policy_engine or LoanPolicyEngine()

    def assess_application(self, application: LoanApplication) -> dict[str, Any]:
        prediction = self.__risk_analyzer.analyze(application)
        financials = self.__policy_engine.evaluate(application)
        base_rec = self.__advisor.generate_recommendation(application, prediction)

        policy_note = (
            "Policy check: Passed."
            if financials["policy_passed"]
            else "Policy alerts: " + " ".join(financials["policy_flags"])
        )
        recommendation = (
            f"{base_rec} "
            f"[Est. EMI: ₹{financials['monthly_emi']:,.0f}/mo | "
            f"DTI: {financials['dti_percent']:.1f}% | {policy_note}]"
        )
        report = self.__report_generator.generate_report(
            application, prediction, financials, recommendation
        )
        return {
            "prediction": prediction,
            "financials": financials,
            "recommendation": recommendation,
            "report": report,
        }

    def assess_from_dict(self, data: dict[str, Any]) -> dict[str, Any]:
        application = LoanApplication.from_dict(data)
        result = self.assess_application(application)
        prediction = result["prediction"]
        return {
            "risk_level": prediction["risk_level"],
            "risk_score": prediction.get("risk_score"),
            "probabilities": prediction.get("probabilities"),
            "model_name": prediction.get("model_name"),
            "financials": result["financials"],
            "recommendation": result["recommendation"],
            "report": result["report"],
        }


def create_gui_predictor(system: CreditRiskSystem):
    def predict_for_gui(application_data: dict[str, Any]) -> dict[str, Any]:
        return system.assess_from_dict(application_data)

    return predict_for_gui
