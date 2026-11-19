"""OOP backend package for the loan credit-risk assessment project."""

from .decision_advisor import DecisionAdvisor
from .models import (
    Applicant,
    ApplicantFactory,
    LoanApplication,
    SalariedApplicant,
    SelfEmployedApplicant,
    StudentApplicant,
    UnemployedApplicant,
)
from .report_generator import ReportGenerator
from .risk_analyzer import RiskAnalyzer
from .system import CreditRiskSystem, create_gui_predictor

__all__ = [
    "Applicant",
    "ApplicantFactory",
    "CreditRiskSystem",
    "DecisionAdvisor",
    "LoanApplication",
    "ReportGenerator",
    "RiskAnalyzer",
    "SalariedApplicant",
    "SelfEmployedApplicant",
    "StudentApplicant",
    "UnemployedApplicant",
    "create_gui_predictor",
]