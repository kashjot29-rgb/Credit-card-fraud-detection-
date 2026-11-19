# Credit Risk Assessment System (Python OOP + ML)

A team OOP project combining a **CustomTkinter + SQLite desktop app** and a **FastAPI + Vercel web deployment** around one shared Python OOP core.

## Team Contributions
- **Dhruv** (`dhruv_gui_storage.py`): CustomTkinter desktop interface and SQLite persistence (`ApplicationDatabase`, `CreditRiskApp`).
- **Yuvraj** (`core_oops/`): Domain OOP layer — `Applicant` inheritance hierarchy, `ApplicantFactory`, `LoanApplication` composition, `DecisionAdvisor`, `ReportGenerator`, and `CreditRiskSystem` facade.
- **Nakul** (`nakul_ml.py`): Polymorphic ML models (`CreditRiskModel` ABC -> `LogisticRiskModel`, `RandomForestRiskModel`) injected into `RiskAnalyzer`.
- **Kashjot** (`kashjot_financials.py`, `api/index.py`, `public/index.html`): Core financial ratios (reducing-balance EMI, Debt-to-Income %), polymorphic `PolicyRule` banking guardrails (`LoanPolicyEngine`), FastAPI backend, and live Vercel web portal.

## Run Locally (Desktop GUI)
pip install -r oops_project/requirements-desktop.txt
python oops_project/run_desktop.py

## Run Locally (Web API)
pip install -r oops_project/requirements.txt uvicorn
uvicorn oops_project.api.index:app --reload
