"""kashjot_financials.py — Core financial math & policy guardrails (Kashjot)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from yuvraj_oop.models import LoanApplication


@dataclass(frozen=True)
class FinancialMetrics:
    """Immutable financial ratios calculated from a LoanApplication."""

    monthly_emi: float
    monthly_income: float
    dti_percent: float       # Debt-to-Income %
    lti_ratio: float         # Loan-to-Income ratio

    @classmethod
    def from_application(
        cls,
        application: LoanApplication,
        annual_interest_rate: float = 0.105,
    ) -> "FinancialMetrics":
        principal = application.loan_amount
        months = application.loan_term_months
        monthly_rate = annual_interest_rate / 12

        if monthly_rate == 0:
            emi = principal / months
        else:
            factor = (1 + monthly_rate) ** months
            emi = principal * monthly_rate * factor / (factor - 1)

        monthly_income = application.applicant.annual_income / 12
        monthly_existing_debt = application.applicant.existing_debt / 12

        if monthly_income <= 0:
            dti_percent = 100.0
            lti_ratio = 99.0
        else:
            dti_percent = min(((monthly_existing_debt + emi) / monthly_income) * 100, 100.0)
            lti_ratio = principal / application.applicant.annual_income

        return cls(
            monthly_emi=round(emi, 2),
            monthly_income=round(monthly_income, 2),
            dti_percent=round(dti_percent, 1),
            lti_ratio=round(lti_ratio, 2),
        )


class PolicyRule(ABC):
    """Abstract banking policy guardrail (Abstraction + Polymorphism)."""

    @abstractmethod
    def check(self, application: LoanApplication, metrics: FinancialMetrics) -> str | None:
        """Return a warning message if violated, otherwise None."""


class MinCreditScoreRule(PolicyRule):
    def __init__(self, min_score: int = 580) -> None:
        self.min_score = min_score

    def check(self, application: LoanApplication, metrics: FinancialMetrics) -> str | None:
        if application.applicant.credit_score < self.min_score:
            return f"Credit score ({application.applicant.credit_score}) is below policy minimum ({self.min_score})."
        return None


class MaxDebtToIncomeRule(PolicyRule):
    def __init__(self, max_dti_percent: float = 55.0) -> None:
        self.max_dti_percent = max_dti_percent

    def check(self, application: LoanApplication, metrics: FinancialMetrics) -> str | None:
        if metrics.dti_percent > self.max_dti_percent:
            return f"Debt-to-Income ({metrics.dti_percent:.1f}%) exceeds safe ceiling ({self.max_dti_percent:.0f}%)."
        return None


class EmploymentStabilityRule(PolicyRule):
    def check(self, application: LoanApplication, metrics: FinancialMetrics) -> str | None:
        if application.applicant.employment_type == "Unemployed" and application.loan_amount > 100_000:
            return "Unemployed applicant requesting a loan above ₹1,00,000 requires a co-signer."
        return None


class LoanPolicyEngine:
    """Evaluates core financial metrics and runs all policy rules polymorphically."""

    def __init__(self, rules: list[PolicyRule] | None = None) -> None:
        self._rules: list[PolicyRule] = rules or [
            MinCreditScoreRule(),
            MaxDebtToIncomeRule(),
            EmploymentStabilityRule(),
        ]

    def evaluate(self, application: LoanApplication) -> dict:
        metrics = FinancialMetrics.from_application(application)
        flags = []
        for rule in self._rules:
            warning = rule.check(application, metrics)
            if warning:
                flags.append(warning)

        return {
            "monthly_emi": metrics.monthly_emi,
            "monthly_income": metrics.monthly_income,
            "dti_percent": metrics.dti_percent,
            "lti_ratio": metrics.lti_ratio,
            "policy_passed": len(flags) == 0,
            "policy_flags": flags,
        }
