"""GUI and SQLite storage module for the team's loan credit-risk OOP project.

The ML/OOP backend is injected through `predictor` so this module can be
integrated without depending on the other teammates' files during development.

Expected predictor interface:
    def predictor(application: dict) -> dict:
        return {
            "risk_level": "Low" | "Medium" | "High",
            "risk_score": 0-100,                 # optional; higher = more risk
            "probabilities": {                  # optional
                "Low": 0.80, "Medium": 0.15, "High": 0.05
            },
            "recommendation": "..."             # optional
        }
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Optional

import customtkinter as ctk
from tkinter import messagebox

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.patches import FancyBboxPatch


RISK_LEVELS = ("Low", "Medium", "High")


class ApplicationDatabase:
    """Small SQLite data layer for saving applications and their predictions."""

    def __init__(self, database_path: str | Path = "credit_risk_applications.db") -> None:
        self.database_path = str(database_path)
        self._create_tables()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _create_tables(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS applications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    full_name TEXT NOT NULL,
                    age INTEGER NOT NULL,
                    annual_income REAL NOT NULL,
                    employment_type TEXT NOT NULL,
                    loan_amount REAL NOT NULL,
                    loan_term_months INTEGER NOT NULL,
                    credit_score INTEGER NOT NULL,
                    existing_debt REAL NOT NULL,
                    dependents INTEGER NOT NULL,
                    risk_level TEXT,
                    risk_score REAL,
                    prediction_json TEXT,
                    created_at TEXT NOT NULL
                )
                """
            )

    def insert_application(
        self,
        application: dict[str, Any],
        prediction: Optional[dict[str, Any]] = None,
    ) -> int:
        prediction = prediction or {}
        prediction_json = json.dumps(prediction, default=self._json_default) if prediction else None

        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO applications (
                    full_name, age, annual_income, employment_type,
                    loan_amount, loan_term_months, credit_score,
                    existing_debt, dependents, risk_level, risk_score,
                    prediction_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    application["full_name"],
                    application["age"],
                    application["annual_income"],
                    application["employment_type"],
                    application["loan_amount"],
                    application["loan_term_months"],
                    application["credit_score"],
                    application["existing_debt"],
                    application["dependents"],
                    prediction.get("risk_level"),
                    prediction.get("risk_score"),
                    prediction_json,
                    datetime.now().isoformat(timespec="seconds"),
                ),
            )
            return int(cursor.lastrowid)

    def update_prediction(self, record_id: int, prediction: dict[str, Any]) -> None:
        prediction_json = json.dumps(prediction, default=self._json_default)
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE applications
                SET risk_level = ?, risk_score = ?, prediction_json = ?
                WHERE id = ?
                """,
                (
                    prediction.get("risk_level"),
                    prediction.get("risk_score"),
                    prediction_json,
                    record_id,
                ),
            )

    def get_recent_applications(self, limit: int = 8) -> list[sqlite3.Row]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, full_name, loan_amount, risk_level, created_at
                FROM applications
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return rows

    @staticmethod
    def _json_default(value: Any) -> Any:
        # Handles common NumPy scalar values returned by scikit-learn.
        if hasattr(value, "item"):
            return value.item()
        return str(value)


class CreditRiskApp(ctk.CTk):
    """CustomTkinter front end. Pass a backend predictor when it is ready."""

    def __init__(
        self,
        predictor: Optional[Callable[[dict[str, Any]], dict[str, Any]]] = None,
        db_path: str | Path = "credit_risk_applications.db",
    ) -> None:
        super().__init__()
        self.title("Credit Risk Assessment System")
        self.geometry("1180x780")
        self.minsize(1050, 700)

        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        self.predictor = predictor
        self.database = ApplicationDatabase(db_path)
        self.last_prediction: Optional[dict[str, Any]] = None
        self.last_application: Optional[dict[str, Any]] = None
        self.last_saved_record_id: Optional[int] = None
        self.last_saved_application: Optional[dict[str, Any]] = None

        self._build_layout()
        self._refresh_history()

    # ---------------------------- UI construction ----------------------------

    def _build_layout(self) -> None:
        self.grid_columnconfigure(0, weight=5)
        self.grid_columnconfigure(1, weight=6)
        self.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=24, pady=(18, 8))
        ctk.CTkLabel(
            header,
            text="CREDIT RISK ASSESSMENT",
            font=ctk.CTkFont(size=25, weight="bold"),
        ).pack(anchor="w")
        ctk.CTkLabel(
            header,
            text="Applicant details  •  Risk prediction  •  Application records",
            font=ctk.CTkFont(size=13),
            text_color=("gray35", "gray70"),
        ).pack(anchor="w", pady=(3, 0))

        self.form_panel = ctk.CTkScrollableFrame(self, label_text="CUSTOMER INPUT FORM")
        self.form_panel.grid(row=1, column=0, sticky="nsew", padx=(24, 10), pady=12)
        self.form_panel.grid_columnconfigure(0, weight=1)

        self.dashboard_panel = ctk.CTkFrame(self)
        self.dashboard_panel.grid(row=1, column=1, sticky="nsew", padx=(10, 24), pady=12)
        self.dashboard_panel.grid_columnconfigure(0, weight=1)
        self.dashboard_panel.grid_rowconfigure(2, weight=1)

        self._build_form()
        self._build_dashboard()

    def _add_entry(
        self,
        parent: ctk.CTkFrame,
        label: str,
        key: str,
        placeholder: str,
    ) -> None:
        block = ctk.CTkFrame(parent, fg_color="transparent")
        block.pack(fill="x", padx=14, pady=(5, 4))
        ctk.CTkLabel(block, text=label, anchor="w").pack(fill="x", pady=(0, 4))
        entry = ctk.CTkEntry(block, placeholder_text=placeholder, height=36)
        entry.pack(fill="x")
        self.entries[key] = entry

    def _build_form(self) -> None:
        self.entries: dict[str, ctk.CTkEntry] = {}

        self._add_entry(self.form_panel, "Full name", "full_name", "e.g. Aarav Sharma")
        self._add_entry(self.form_panel, "Age (years)", "age", "e.g. 25")
        self._add_entry(self.form_panel, "Annual income (₹)", "annual_income", "e.g. 800000")

        employment_block = ctk.CTkFrame(self.form_panel, fg_color="transparent")
        employment_block.pack(fill="x", padx=14, pady=(5, 4))
        ctk.CTkLabel(employment_block, text="Employment type", anchor="w").pack(fill="x", pady=(0, 4))
        self.employment_menu = ctk.CTkOptionMenu(
            employment_block,
            values=["Salaried", "Self-employed", "Business", "Student", "Unemployed"],
            height=36,
        )
        self.employment_menu.pack(fill="x")

        self._add_entry(self.form_panel, "Loan amount requested (₹)", "loan_amount", "e.g. 500000")
        self._add_entry(self.form_panel, "Loan term (months)", "loan_term_months", "e.g. 36")
        self._add_entry(self.form_panel, "Credit score (300–900)", "credit_score", "e.g. 720")
        self._add_entry(self.form_panel, "Existing debt (₹)", "existing_debt", "e.g. 100000")
        self._add_entry(self.form_panel, "Number of dependents", "dependents", "e.g. 2")

        button_row = ctk.CTkFrame(self.form_panel, fg_color="transparent")
        button_row.pack(fill="x", padx=14, pady=(18, 10))
        button_row.grid_columnconfigure(0, weight=1)
        button_row.grid_columnconfigure(1, weight=1)
        ctk.CTkButton(
            button_row,
            text="Save applicant",
            command=self._save_without_prediction,
            height=40,
        ).grid(row=0, column=0, sticky="ew", padx=(0, 5))
        ctk.CTkButton(
            button_row,
            text="Assess risk",
            command=self._run_prediction,
            height=40,
        ).grid(row=0, column=1, sticky="ew", padx=(5, 0))
        ctk.CTkButton(
            self.form_panel,
            text="Clear form",
            command=self._clear_form,
            fg_color="transparent",
            border_width=1,
            height=34,
        ).pack(fill="x", padx=14, pady=(0, 14))

        ctk.CTkLabel(
            self.form_panel,
            text="Note: The form fields are a starter schema. Map or rename them to match the final ML dataset before integration.",
            justify="left",
            wraplength=390,
            font=ctk.CTkFont(size=11),
            text_color=("gray40", "gray65"),
        ).pack(fill="x", padx=14, pady=(0, 15))

    def _build_dashboard(self) -> None:
        result_card = ctk.CTkFrame(self.dashboard_panel)
        result_card.grid(row=0, column=0, sticky="ew", padx=14, pady=(14, 8))
        result_card.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            result_card,
            text="RISK ASSESSMENT RESULT",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=14, pady=(12, 2))
        self.risk_label = ctk.CTkLabel(
            result_card,
            text="Awaiting applicant details",
            font=ctk.CTkFont(size=23, weight="bold"),
        )
        self.risk_label.grid(row=1, column=0, sticky="w", padx=14, pady=(4, 0))
        self.score_label = ctk.CTkLabel(
            result_card,
            text="Risk score: —",
            font=ctk.CTkFont(size=13),
            text_color=("gray35", "gray70"),
        )
        self.score_label.grid(row=2, column=0, sticky="w", padx=14, pady=(3, 0))
        self.recommendation_label = ctk.CTkLabel(
            result_card,
            text="Run the connected ML model to see its result here.",
            justify="left",
            wraplength=490,
        )
        self.recommendation_label.grid(row=3, column=0, sticky="w", padx=14, pady=(6, 12))

        chart_frame = ctk.CTkFrame(self.dashboard_panel)
        chart_frame.grid(row=1, column=0, sticky="nsew", padx=14, pady=8)
        chart_frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            chart_frame,
            text="RISK LEVEL VISUALIZATION",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(anchor="w", padx=12, pady=(10, 0))
        self.risk_figure = Figure(figsize=(6.0, 2.0), dpi=90)
        self.risk_axes = self.risk_figure.add_subplot(111)
        self.risk_canvas = FigureCanvasTkAgg(self.risk_figure, master=chart_frame)
        self.risk_canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=(0, 6))
        self._draw_risk_visual(None, None)

        history_frame = ctk.CTkFrame(self.dashboard_panel)
        history_frame.grid(row=2, column=0, sticky="nsew", padx=14, pady=(8, 14))
        history_frame.grid_columnconfigure(0, weight=1)
        history_frame.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(
            history_frame,
            text="RECENT APPLICATIONS",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=12, pady=(10, 5))
        self.history_box = ctk.CTkTextbox(history_frame, height=150, activate_scrollbars=True)
        self.history_box.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.history_box.configure(state="disabled")

    # ------------------------------ Form logic -------------------------------

    def _read_application(self) -> dict[str, Any]:
        def number(key: str, cast: type, label: str) -> Any:
            raw = self.entries[key].get().strip().replace(",", "")
            if not raw:
                raise ValueError(f"Please enter {label}.")
            try:
                return cast(raw)
            except ValueError as exc:
                raise ValueError(f"{label} must be a valid number.") from exc

        full_name = self.entries["full_name"].get().strip()
        if not full_name:
            raise ValueError("Please enter the applicant's name.")

        application = {
            "full_name": full_name,
            "age": number("age", int, "age"),
            "annual_income": number("annual_income", float, "annual income"),
            "employment_type": self.employment_menu.get(),
            "loan_amount": number("loan_amount", float, "loan amount"),
            "loan_term_months": number("loan_term_months", int, "loan term"),
            "credit_score": number("credit_score", int, "credit score"),
            "existing_debt": number("existing_debt", float, "existing debt"),
            "dependents": number("dependents", int, "number of dependents"),
        }

        if not 18 <= application["age"] <= 100:
            raise ValueError("Age must be between 18 and 100.")
        if application["annual_income"] <= 0:
            raise ValueError("Annual income must be greater than zero.")
        if application["loan_amount"] <= 0:
            raise ValueError("Loan amount must be greater than zero.")
        if application["loan_term_months"] <= 0:
            raise ValueError("Loan term must be greater than zero months.")
        if not 300 <= application["credit_score"] <= 900:
            raise ValueError("Credit score must be between 300 and 900.")
        if application["existing_debt"] < 0 or application["dependents"] < 0:
            raise ValueError("Existing debt and dependents cannot be negative.")

        return application

    def _save_without_prediction(self) -> None:
        try:
            application = self._read_application()
            record_id = self.database.insert_application(application)
            self.last_application = application
            self.last_saved_record_id = record_id
            self.last_saved_application = application.copy()
            self._refresh_history()
            messagebox.showinfo("Saved", f"Applicant saved successfully. Record ID: {record_id}")
        except ValueError as error:
            messagebox.showwarning("Check applicant details", str(error))
        except sqlite3.Error as error:
            messagebox.showerror("Database error", f"Could not save the applicant.\n\n{error}")

    def _run_prediction(self) -> None:
        if self.predictor is None:
            messagebox.showwarning(
                "Backend not connected",
                "The GUI is ready, but the ML predictor has not been connected yet.\n\n"
                "Pass your team's prediction function to CreditRiskApp(predictor=...).",
            )
            return

        try:
            application = self._read_application()
            raw_prediction = self.predictor(application)
            prediction = self._normalise_prediction(raw_prediction)
            if self.last_saved_record_id is not None and self.last_saved_application == application:
                self.database.update_prediction(self.last_saved_record_id, prediction)
                record_id = self.last_saved_record_id
            else:
                record_id = self.database.insert_application(application, prediction)
                self.last_saved_record_id = record_id
                self.last_saved_application = application.copy()
            self.last_application = application
            self.last_prediction = prediction
            self._display_prediction(application, prediction)
            self._refresh_history()
            messagebox.showinfo("Assessment complete", f"Prediction saved. Record ID: {record_id}")
        except ValueError as error:
            messagebox.showwarning("Check applicant details", str(error))
        except sqlite3.Error as error:
            messagebox.showerror("Database error", f"Prediction completed, but could not save it.\n\n{error}")
        except Exception as error:  # Show backend integration errors rather than crashing the GUI.
            messagebox.showerror("Prediction error", f"The connected predictor returned an error.\n\n{error}")

    @staticmethod
    def _normalise_prediction(result: Any) -> dict[str, Any]:
        if not isinstance(result, dict):
            raise ValueError(
                "The predictor must return a dictionary containing at least 'risk_level'."
            )

        risk_level = str(result.get("risk_level", "")).strip().title()
        if risk_level not in RISK_LEVELS:
            raise ValueError("Predictor risk_level must be Low, Medium, or High.")

        normalised: dict[str, Any] = {
            "risk_level": risk_level,
            "recommendation": str(result.get("recommendation") or ""),
        }

        if result.get("risk_score") is not None:
            score = float(result["risk_score"])
            if not 0 <= score <= 100:
                raise ValueError("risk_score must be between 0 and 100.")
            normalised["risk_score"] = score

        probabilities = result.get("probabilities")
        if probabilities is not None:
            if not isinstance(probabilities, dict):
                raise ValueError("probabilities must be a dictionary, when provided.")
            cleaned: dict[str, float] = {}
            for level in RISK_LEVELS:
                if level in probabilities:
                    value = float(probabilities[level])
                    if not 0 <= value <= 1:
                        raise ValueError("Each probability must be between 0 and 1.")
                    cleaned[level] = value
            if cleaned:
                normalised["probabilities"] = cleaned

        return normalised

    # ------------------------------ Dashboard --------------------------------

    def _display_prediction(
        self,
        application: dict[str, Any],
        prediction: dict[str, Any],
    ) -> None:
        risk = prediction["risk_level"]
        self.risk_label.configure(text=f"{risk} Risk")

        if "risk_score" in prediction:
            self.score_label.configure(text=f"Risk score: {prediction['risk_score']:.1f}/100")
        else:
            self.score_label.configure(text="Risk score: not supplied by model")

        recommendation = prediction.get("recommendation") or "No recommendation supplied by the model."
        self.recommendation_label.configure(text=recommendation)
        self._draw_risk_visual(risk, prediction.get("probabilities"))

    def _draw_risk_visual(
        self,
        selected_risk: Optional[str],
        probabilities: Optional[dict[str, float]],
    ) -> None:
        ax = self.risk_axes
        ax.clear()
        ax.set_xlim(0, 3)
        ax.set_ylim(0, 1)
        ax.axis("off")

        # A categorical gauge is used because the model may return only a class,
        # not a calibrated numerical probability or score.
        fills = {"Low": "#2E8B57", "Medium": "#E0A12D", "High": "#C94C4C"}
        for index, level in enumerate(RISK_LEVELS):
            active = level == selected_risk
            ax.add_patch(
                FancyBboxPatch(
                    (index + 0.06, 0.38), 0.88, 0.34,
                    boxstyle="round,pad=0.03,rounding_size=0.08",
                    facecolor=fills[level] if active else "#D9DDE3",
                    edgecolor=fills[level] if active else "#B8BEC7",
                    linewidth=2 if active else 1,
                    alpha=1.0 if active else 0.65,
                )
            )
            ax.text(
                index + 0.5, 0.55, level,
                ha="center", va="center",
                fontsize=11, fontweight="bold",
                color="white" if active else "#30343B",
            )

        if probabilities:
            pieces = [f"{level}: {probabilities[level] * 100:.1f}%" for level in RISK_LEVELS if level in probabilities]
            note = "Model probabilities  •  " + "   |   ".join(pieces)
        elif selected_risk:
            note = f"Predicted category: {selected_risk} risk"
        else:
            note = "The predicted category will be highlighted here"
        ax.text(1.5, 0.16, note, ha="center", va="center", fontsize=8.5, color="#555B65")
        self.risk_figure.tight_layout(pad=0.5)
        self.risk_canvas.draw_idle()

    def _refresh_history(self) -> None:
        rows = self.database.get_recent_applications()
        lines = []
        for row in rows:
            timestamp = row["created_at"].replace("T", " ")
            risk = row["risk_level"] or "Not assessed"
            lines.append(
                f"#{row['id']}  {row['full_name']}  |  ₹{row['loan_amount']:,.0f}  |  {risk}\n"
                f"     {timestamp}"
            )
        if not lines:
            content = "No saved applications yet."
        else:
            content = "\n\n".join(lines)

        self.history_box.configure(state="normal")
        self.history_box.delete("1.0", "end")
        self.history_box.insert("1.0", content)
        self.history_box.configure(state="disabled")

    def _clear_form(self) -> None:
        for entry in self.entries.values():
            entry.delete(0, "end")
        self.employment_menu.set("Salaried")
        self.risk_label.configure(text="Awaiting applicant details")
        self.score_label.configure(text="Risk score: —")
        self.recommendation_label.configure(text="Run the connected ML model to see its result here.")
        self.last_prediction = None
        self.last_application = None
        self.last_saved_record_id = None
        self.last_saved_application = None
        self._draw_risk_visual(None, None)


if __name__ == "__main__":
    # Run the interface before the ML module is ready. Saving applicants works;
    # the Assess risk button becomes active once a predictor is passed in.
    app = CreditRiskApp()
    app.mainloop()
