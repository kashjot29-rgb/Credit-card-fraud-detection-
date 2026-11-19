"""main.py — Runs Dhruv's Desktop GUI connected to Yuvraj, Nakul, and Kashjot."""

from dhruv_gui_storage import CreditRiskApp
from nakul_ml import predict_application
from yuvraj_oop import CreditRiskSystem, RiskAnalyzer, create_gui_predictor

if __name__ == "__main__":
    backend = CreditRiskSystem(RiskAnalyzer(predict_application))
    app = CreditRiskApp(predictor=create_gui_predictor(backend))
    app.mainloop()
