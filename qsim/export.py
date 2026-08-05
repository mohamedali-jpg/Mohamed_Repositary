from __future__ import annotations

import csv
import json

from .models import Questionnaire


def responses_to_rows(questionnaire: Questionnaire, personas: list, responses: list) -> list:
    persona_by_id = {p.id: p for p in personas}
    rows = []
    for r in responses:
        p = persona_by_id[r.persona_id]
        row = {
            "respondent_id": r.persona_id,
            "age": p.age,
            "age_group": p.age_group,
            "gender": p.gender,
            "region": p.region,
            "tenure_years": p.tenure_years,
        }
        for qid, val in r.answers.items():
            if isinstance(val, list):
                row[qid] = "; ".join(val)
            else:
                row[qid] = val if val is not None else ""
        rows.append(row)
    return rows


def write_csv(path: str, rows: list) -> None:
    if not rows:
        return
    fieldnames = list(rows[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: str, questionnaire: Questionnaire, personas: list, responses: list) -> None:
    persona_by_id = {p.id: p.__dict__ for p in personas}
    data = {
        "questionnaire": questionnaire.title,
        "n_respondents": len(responses),
        "responses": [
            {"respondent": persona_by_id[r.persona_id], "answers": r.answers} for r in responses
        ],
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)
