from __future__ import annotations

from collections import Counter
from statistics import mean, pstdev

from .models import Questionnaire, QuestionType


def summarize(questionnaire: Questionnaire, responses: list) -> dict:
    summary = {"n": len(responses), "questions": {}}
    for q in questionnaire.questions:
        values = [r.answers.get(q.id) for r in responses]
        non_null = [v for v in values if v is not None]
        entry = {
            "text": q.text,
            "type": q.type.value,
            "n_answered": len(non_null),
            "n_skipped": len(values) - len(non_null),
        }

        if q.type in (QuestionType.LIKERT, QuestionType.NPS, QuestionType.NUMERIC):
            if non_null:
                entry["mean"] = round(mean(non_null), 2)
                entry["stdev"] = round(pstdev(non_null), 2) if len(non_null) > 1 else 0.0
                entry["min"] = min(non_null)
                entry["max"] = max(non_null)
            if q.type == QuestionType.NPS and non_null:
                promoters = sum(1 for v in non_null if v >= 9)
                detractors = sum(1 for v in non_null if v <= 6)
                entry["nps_score"] = round((promoters - detractors) / len(non_null) * 100, 1)

        elif q.type in (QuestionType.SINGLE_CHOICE, QuestionType.YES_NO):
            counts = Counter(non_null)
            entry["distribution"] = dict(counts.most_common())

        elif q.type == QuestionType.MULTI_CHOICE:
            counts = Counter()
            for v in non_null:
                counts.update(v)
            entry["distribution"] = dict(counts.most_common())

        elif q.type == QuestionType.OPEN_TEXT:
            entry["sample_answers"] = non_null[:5]

        summary["questions"][q.id] = entry
    return summary


def format_summary_text(summary: dict) -> str:
    lines = [f"Responses: {summary['n']}", ""]
    for qid, entry in summary["questions"].items():
        lines.append(f"[{qid}] {entry['text']} ({entry['type']})")
        if "mean" in entry:
            lines.append(f"  mean={entry['mean']}  stdev={entry['stdev']}  range=[{entry['min']}, {entry['max']}]")
        if "nps_score" in entry:
            lines.append(f"  NPS score: {entry['nps_score']}")
        if "distribution" in entry:
            total = sum(entry["distribution"].values()) or 1
            for k, v in entry["distribution"].items():
                pct = round(v / total * 100, 1)
                lines.append(f"  {k}: {v} ({pct}%)")
        if "sample_answers" in entry:
            lines.append("  sample answers:")
            for s in entry["sample_answers"]:
                lines.append(f"    - {s}")
        lines.append(f"  answered={entry['n_answered']} skipped={entry['n_skipped']}")
        lines.append("")
    return "\n".join(lines)
