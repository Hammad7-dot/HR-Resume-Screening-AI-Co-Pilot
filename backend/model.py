"""
Loads the trained ANN + scaler + feature schema exported from Colab, and
provides prediction, confidence, and SHAP explanation for one candidate
at a time (as the FastAPI endpoints need).
"""
import pickle
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import shap

from features import extract_all_features, to_model_row, KNOWN_CATEGORIES

ARTIFACTS_DIR = Path(__file__).parent / "artifacts"


class FitScoreANN(nn.Module):
    """Must match the architecture trained in the Colab ANN notebook exactly."""

    def __init__(self, input_dim, hidden1=32, hidden2=16, dropout=0.1):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden1),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden1, hidden2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden2, 1),
        )

    def forward(self, x):
        return self.net(x)


class ResumeScorer:
    def __init__(self):
        with open(ARTIFACTS_DIR / "feature_names.pkl", "rb") as f:
            self.feature_names = pickle.load(f)
        with open(ARTIFACTS_DIR / "scaler.pkl", "rb") as f:
            self.scaler = pickle.load(f)

        self.model = FitScoreANN(input_dim=len(self.feature_names))
        self.model.load_state_dict(torch.load(ARTIFACTS_DIR / "fit_score_ann.pt", map_location="cpu"))
        self.model.eval()

        # Calibration bounds from the training notebook's observed MC-Dropout std
        # range — confidence is scaled relative to THIS range, not a guessed constant.
        calib_path = ARTIFACTS_DIR / "confidence_calibration.pkl"
        if calib_path.exists():
            with open(calib_path, "rb") as f:
                calib = pickle.load(f)
            self.std_min = calib["std_min"]
            self.std_max = calib["std_max"]
        else:
            self.std_min, self.std_max = 0.0, 10.0  # fallback if calibration file is missing

        self._background = self._build_background()
        self.explainer = shap.DeepExplainer(self.model, self._background)

    def _build_background(self, n=100):
        """Reconstruct a scaled background sample from the training CSV for SHAP."""
        df = pd.read_csv(ARTIFACTS_DIR / "processed_features.csv")
        cat_dummies = pd.get_dummies(df["Category"], prefix="cat")
        numeric_cols = ["years_experience", "education_level", "certifications_count", "skills_count"]
        X = pd.concat([df[numeric_cols], cat_dummies], axis=1)
        X = X.reindex(columns=self.feature_names, fill_value=0)
        sample = X.sample(n=min(n, len(X)), random_state=42)
        scaled = self.scaler.transform(sample.values)
        return torch.tensor(scaled, dtype=torch.float32)

    @staticmethod
    def fit_category(score: float) -> str:
        if score >= 60:
            return "Strong Fit"
        elif score >= 30:
            return "Moderate Fit"
        return "Weak Fit"

    _FEATURE_PHRASES = {
        "skills_count": ("a strong match on relevant skills", "few relevant skills detected in the resume"),
        "years_experience": ("solid years of experience", "limited years of experience"),
        "education_level": ("a strong education background", "a lighter education background"),
        "certifications_count": ("relevant certifications", "no notable certifications"),
    }

    @classmethod
    def _generate_narration(cls, fit_score, fit_category, top_features, raw_features):
        """Template-based (no LLM) plain-English summary of why a resume scored as it did."""
        numeric_pairs = [
            (f["feature"], f["impact"]) for f in top_features if not f["feature"].startswith("cat_")
        ]
        numeric_pairs.sort(key=lambda t: abs(t[1]), reverse=True)

        if fit_category == "Strong Fit":
            lead_in = f"Scored well ({fit_score}/100)"
        elif fit_category == "Moderate Fit":
            lead_in = f"Scored moderately ({fit_score}/100)"
        else:
            lead_in = f"Scored low ({fit_score}/100)"

        phrases = []
        for feature, impact in numeric_pairs[:2]:
            pair = cls._FEATURE_PHRASES.get(feature)
            if not pair:
                continue
            phrases.append((pair[0] if impact >= 0 else pair[1], impact >= 0))

        if not phrases:
            return f"{lead_in} — no single feature stood out as decisive; consider reviewing the resume manually."

        if len(phrases) == 1:
            return f"{lead_in} mainly because of {phrases[0][0]}."
        connector = "and" if phrases[0][1] == phrases[1][1] else "despite"
        return f"{lead_in} mainly because of {phrases[0][0]}, {connector} {phrases[1][0]}."

    def score_resume(self, resume_text: str, category: str) -> dict:
        if category not in KNOWN_CATEGORIES:
            category = "GENERAL"  # falls through to all-zero cat_* row; still scoreable

        raw_features = extract_all_features(resume_text, category)
        row = to_model_row(raw_features, self.feature_names)
        x = np.array([row], dtype=np.float32)
        x_scaled = self.scaler.transform(x)
        x_tensor = torch.tensor(x_scaled, dtype=torch.float32)

        mean_score, confidence = self._predict_with_confidence(x_tensor)
        mean_score = float(np.clip(mean_score, 0, 100))

        top_features = self._explain(x_tensor)
        fit_category = self.fit_category(mean_score)
        narration = self._generate_narration(round(mean_score, 1), fit_category, top_features, raw_features)

        return {
            "fit_score": round(mean_score, 1),
            "fit_category": fit_category,
            "confidence": round(float(confidence), 1),
            "top_features": top_features,
            "narration": narration,
            "raw_features": {
                "years_experience": raw_features["years_experience"],
                "education_level": raw_features["education_level"],
                "certifications_count": raw_features["certifications_count"],
                "skills_found": raw_features["skills_found"],
            },
        }

    def _predict_with_confidence(self, x_tensor, n_passes=30):
        self.model.train()  # keep dropout active
        preds = []
        with torch.no_grad():
            for _ in range(n_passes):
                preds.append(self.model(x_tensor).squeeze().item())
        self.model.eval()
        preds = np.array(preds)
        mean_pred = preds.mean()
        std_pred = preds.std()

        # Scale relative to the OBSERVED std range from training, not an arbitrary
        # constant — keeps confidence spread across the full 0-100 range instead
        # of collapsing everything into a narrow low band.
        if self.std_max > self.std_min:
            confidence = 100 * (1 - (std_pred - self.std_min) / (self.std_max - self.std_min))
        else:
            confidence = 100.0
        confidence = float(np.clip(confidence, 0, 100))
        return mean_pred, confidence

    def _explain(self, x_tensor, top_k=3):
        shap_values = self.explainer.shap_values(x_tensor)
        shap_values = np.array(shap_values).squeeze()
        pairs = sorted(zip(self.feature_names, shap_values.tolist()), key=lambda t: abs(t[1]), reverse=True)
        return [{"feature": f, "impact": round(v, 2)} for f, v in pairs[:top_k]]


# Singleton — loaded once at app startup, reused across requests.
scorer = ResumeScorer()
