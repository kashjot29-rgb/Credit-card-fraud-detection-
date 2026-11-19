"""Adapter between LoanApplication objects and the ML predictor."""

from __future__ import annotations

from typing import Any, Callable

from .models import LoanApplication

VALID_RISK_LEVELS = {"low": "Low", "medium": "Medium", "high": "High"}
Predictor = Callable[[dict[str, Any]], dict[str, Any]]


class RiskAnalyzer:
    """Calls an injected ML prediction function (Dependency Injection)."""

    def __init__(self, predictor: Predictor) -> None:
        if not callable(predictor):
            raise TypeError("predictor must be callable.")
        self.__predictor = predictor

    def analyze(self, application: LoanApplication) -> dict[str, Any]:
        if not isinstance(application, LoanApplication):
            raise TypeError("analyze() expects a LoanApplication object.")

        raw = self.__predictor(application.to_dict())
        level = VALID_RISK_LEVELS.get(str(raw.get("risk_level", "")).strip().lower())
        if level is None:
            raise ValueError("ML predictor must return risk_level: Low, Medium, or High.")

        risk_score = raw.get("risk_score")
        if risk_score is not None:
            risk_score = float(risk_score)
            if not 0 <= risk_score <= 100:
                raise ValueError("risk_score must be between 0 and 100.")

        return {
            "risk_level": level,
            "risk_score": risk_score,
            "probabilities": raw.get("probabilities"),
            "model_name": raw.get("model_name", "Scikit-learn model"),
        }
