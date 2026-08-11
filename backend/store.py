"""
Minimal persistence layer for candidates + recruiter decisions (the
Human-in-the-Loop audit trail). A JSON file is enough for a hackathon demo;
swap for a real DB later without changing the API shape.
"""
import json
import uuid
from datetime import datetime
from pathlib import Path
from threading import Lock

DATA_FILE = Path(__file__).parent / "data" / "candidates.json"
DATA_FILE.parent.mkdir(exist_ok=True)
_lock = Lock()


def _load() -> dict:
    if not DATA_FILE.exists():
        return {}
    with open(DATA_FILE) as f:
        return json.load(f)


def _save(data: dict):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def add_candidate(filename: str, category: str, prediction: dict) -> dict:
    with _lock:
        data = _load()
        candidate_id = str(uuid.uuid4())[:8]
        record = {
            "id": candidate_id,
            "filename": filename,
            "category": category,
            "prediction": prediction,
            "decision": None,       # "approve" | "reject" | "modify"
            "decision_reason": None,
            "modified_score": None,
            "decided_at": None,
            "uploaded_at": datetime.utcnow().isoformat(),
        }
        data[candidate_id] = record
        _save(data)
        return record


def set_decision(candidate_id: str, decision: str, reason: str, modified_score: float = None) -> dict:
    with _lock:
        data = _load()
        if candidate_id not in data:
            raise KeyError(candidate_id)
        record = data[candidate_id]
        record["decision"] = decision
        record["decision_reason"] = reason
        record["modified_score"] = modified_score
        record["decided_at"] = datetime.utcnow().isoformat()
        data[candidate_id] = record
        _save(data)
        return record


def list_candidates() -> list:
    return list(_load().values())


def get_candidate(candidate_id: str) -> dict:
    return _load().get(candidate_id)


def approved_candidates() -> list:
    return [c for c in list_candidates() if c["decision"] == "approve"]
