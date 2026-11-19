"""Domain models (Encapsulation, Inheritance, Polymorphism, Composition, Factory)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


class Applicant:
    """Base applicant class with private attributes and property getters."""

    def __init__(
        self,
        full_name: str,
        age: int,
        annual_income: float,
        credit_score: int,
        existing_debt: float,
        dependents: int,
        employment_type: str,
    ) -> None:
        name = str(full_name).strip()
        if not name:
            raise ValueError("Applicant name cannot be empty.")
        if not 18 <= int(age) <= 100:
            raise ValueError("Applicant age must be between 18 and 100.")
        if float(annual_income) < 0:
            raise ValueError("Annual income cannot be negative.")
        if not 300 <= int(credit_score) <= 900:
            raise ValueError("Credit score must be between 300 and 900.")
        if float(existing_debt) < 0:
            raise ValueError("Existing debt cannot be negative.")
        if int(dependents) < 0:
            raise ValueError("Dependents cannot be negative.")

        self._full_name = name
        self._age = int(age)
        self._annual_income = float(annual_income)
        self._credit_score = int(credit_score)
        self._existing_debt = float(existing_debt)
        self._dependents = int(dependents)
        self._employment_type = str(employment_type).strip().title()

    @property
    def full_name(self) -> str:
        return self._full_name

    @property
    def age(self) -> int:
        return self._age

    @property
    def annual_income(self) -> float:
        return self._annual_income

    @property
    def credit_score(self) -> int:
        return self._credit_score

    @property
    def existing_debt(self) -> float:
        return self._existing_debt

    @property
    def dependents(self) -> int:
        return self._dependents

    @property
    def employment_type(self) -> str:
        return self._employment_type

    def employment_profile(self) -> str:
        return f"Employment type: {self.employment_type}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "full_name": self.full_name,
            "age": self.age,
            "annual_income": self.annual_income,
            "employment_type": self.employment_type,
            "credit_score": self.credit_score,
            "existing_debt": self.existing_debt,
            "dependents": self.dependents,
        }


class SalariedApplicant(Applicant):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, employment_type="Salaried", **kwargs)

    def employment_profile(self) -> str:
        return "Salaried employee (stable monthly income)"


class SelfEmployedApplicant(Applicant):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, employment_type="Self-employed", **kwargs)

    def employment_profile(self) -> str:
        return "Self-employed / business owner (variable income)"


class StudentApplicant(Applicant):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, employment_type="Student", **kwargs)

    def employment_profile(self) -> str:
        return "Student applicant"


class UnemployedApplicant(Applicant):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, employment_type="Unemployed", **kwargs)

    def employment_profile(self) -> str:
        return "Currently unemployed"


class ApplicantFactory:
    """Factory pattern: builds the right Applicant subclass from form data."""

    @staticmethod
    def from_dict(data: dict[str, Any]) -> Applicant:
        employment = str(data.get("employment_type", "Salaried")).strip().lower()
        common = {
            "full_name": data["full_name"],
            "age": data["age"],
            "annual_income": data["annual_income"],
            "credit_score": data["credit_score"],
            "existing_debt": data["existing_debt"],
            "dependents": data["dependents"],
        }
        if employment == "salaried":
            return SalariedApplicant(**common)
        if employment in {"self-employed", "self employed", "business"}:
            return SelfEmployedApplicant(**common)
        if employment == "student":
            return StudentApplicant(**common)
        if employment == "unemployed":
            return UnemployedApplicant(**common)
        return Applicant(**common, employment_type=str(data.get("employment_type", "Other")))


class LoanApplication:
    """Composition (has-a): a LoanApplication owns one Applicant object."""

    def __init__(
        self,
        applicant: Applicant,
        loan_amount: float,
        loan_term_months: int,
        application_id: str | None = None,
    ) -> None:
        if not isinstance(applicant, Applicant):
            raise TypeError("applicant must be an Applicant object.")
        if float(loan_amount) <= 0:
            raise ValueError("Loan amount must be greater than zero.")
        if int(loan_term_months) <= 0:
            raise ValueError("Loan term must be greater than zero months.")

        self._applicant = applicant
        self._loan_amount = float(loan_amount)
        self._loan_term_months = int(loan_term_months)
        self._application_id = application_id or f"LA-{uuid4().hex[:8].upper()}"
        self._created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")

    @property
    def applicant(self) -> Applicant:
        return self._applicant

    @property
    def loan_amount(self) -> float:
        return self._loan_amount

    @property
    def loan_term_months(self) -> int:
        return self._loan_term_months

    @property
    def application_id(self) -> str:
        return self._application_id

    @property
    def created_at(self) -> str:
        return self._created_at

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.applicant.to_dict(),
            "loan_amount": self.loan_amount,
            "loan_term_months": self.loan_term_months,
            "application_id": self.application_id,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LoanApplication":
        applicant = ApplicantFactory.from_dict(data)
        return cls(
            applicant=applicant,
            loan_amount=data["loan_amount"],
            loan_term_months=data["loan_term_months"],
            application_id=data.get("application_id"),
        )
