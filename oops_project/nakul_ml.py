"""nakul_ml.py — Clean OOP + Scikit-Learn backend matching GUI & Yuvraj's contract."""

from __future__ import annotations

from abc import ABC, abstractmethod
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.preprocessing import StandardScaler


RISK_LABELS = ("Low", "Medium", "High")

EMPLOYMENT_STABILITY = {
    "salaried": 0.90,
    "business": 0.70,
    "self-employed": 0.65,
    "student": 0.35,
    "unemployed": 0.15,
}


def extract_features(application: dict) -> np.ndarray:
    """Convert application dictionary into the ordered numeric feature row."""
    emp_key = str(application.get("employment_type", "Salaried")).strip().lower()
    stability = EMPLOYMENT_STABILITY.get(emp_key, 0.50)

    return np.array([[
        float(application["age"]),
        float(application["annual_income"]),
        float(application["loan_amount"]),
        float(application["loan_term_months"]),
        float(application["credit_score"]),
        float(application["existing_debt"]),
        float(application["dependents"]),
        stability,
    ]], dtype=float)


def make_synthetic_loan_data(rows: int = 4000, seed: int = 42) -> tuple[np.ndarray, np.ndarray]:
    """Generate synthetic Indian loan data matching the 9 form fields."""
    rng = np.random.default_rng(seed)

    age = rng.integers(21, 65, rows)
    annual_income = rng.uniform(180_000, 2_500_000, rows)
    loan_amount = rng.uniform(50_000, 1_500_000, rows)
    loan_term_months = rng.choice([12, 24, 36, 48, 60, 84], size=rows)
    credit_score = np.clip(rng.normal(700, 80, rows), 300, 900)
    existing_debt = rng.uniform(0, 600_000, rows)
    dependents = rng.integers(0, 5, rows)
    stability = rng.choice(list(EMPLOYMENT_STABILITY.values()), size=rows)

    debt_burden = (existing_debt + loan_amount / (loan_term_months / 12)) / annual_income
    raw_risk = (
        -0.025 * (credit_score - 650)
        + 2.2 * debt_burden
        + 0.25 * dependents
        - 1.8 * stability
        + rng.normal(0, 0.4, rows)
    )
    low_cut, high_cut = np.quantile(raw_risk, [1 / 3, 2 / 3])
    labels = np.digitize(raw_risk, [low_cut, high_cut]).astype(int)

    features = np.column_stack([
        age, annual_income, loan_amount, loan_term_months,
        credit_score, existing_debt, dependents, stability,
    ])
    return features, labels


class CreditRiskModel(ABC):
    """Abstract base class for ML models (Abstraction + Polymorphism)."""

    name = "Base Model"

    def __init__(self) -> None:
        self._pipeline: Pipeline | None = None
        self._accuracy: float = 0.0

    @abstractmethod
    def build_estimator(self) -> Pipeline:
        """Return the scikit-learn classifier pipeline."""

    def train(self, x: np.ndarray, y: np.ndarray, seed: int = 42) -> float:
        x_train, x_test, y_train, y_test = train_test_split(
            x, y, test_size=0.25, random_state=seed, stratify=y
        )
        self._pipeline = self.build_estimator()
        self._pipeline.fit(x_train, y_train)
        self._accuracy = float(accuracy_score(y_test, self._pipeline.predict(x_test)))
        return self._accuracy

    def predict(self, features: np.ndarray) -> dict:
        if self._pipeline is None:
            raise RuntimeError("Model has not been trained.")
        probs = self._pipeline.predict_proba(features)[0]
        prob_dict = {label: round(float(probs[i]), 4) for i, label in enumerate(RISK_LABELS)}

        risk_score = round((0.0 * probs[0] + 0.5 * probs[1] + 1.0 * probs[2]) * 100, 1)
        risk_level = RISK_LABELS[int(np.argmax(probs))]

        return {
            "risk_level": risk_level,
            "risk_score": risk_score,
            "probabilities": prob_dict,
            "model_name": f"{self.name} (acc: {self._accuracy:.1%})",
        }


class LogisticRiskModel(CreditRiskModel):
    name = "Logistic Regression"

    def build_estimator(self) -> Pipeline:
        return make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000))


class RandomForestRiskModel(CreditRiskModel):
    name = "Random Forest"

    def build_estimator(self) -> Pipeline:
        return Pipeline([
            ("rf", RandomForestClassifier(n_estimators=80, min_samples_leaf=4, random_state=42))
        ])


_X, _Y = make_synthetic_loan_data()
_ACTIVE_MODEL: CreditRiskModel = RandomForestRiskModel()
_ACTIVE_MODEL.train(_X, _Y)


def predict_application(application: dict) -> dict:
    """Contract expected by Yuvraj's RiskAnalyzer."""
    return _ACTIVE_MODEL.predict(extract_features(application))