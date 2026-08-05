from __future__ import annotations

import json
from dataclasses import dataclass, field, fields
from enum import Enum
from typing import Optional


class QuestionType(str, Enum):
    SINGLE_CHOICE = "single_choice"
    MULTI_CHOICE = "multi_choice"
    LIKERT = "likert"
    NPS = "nps"
    YES_NO = "yes_no"
    NUMERIC = "numeric"
    OPEN_TEXT = "open_text"


@dataclass
class Question:
    id: str
    type: QuestionType
    text: str
    options: Optional[list] = None
    weights: Optional[list] = None
    scale: int = 5
    sentiment_linked: bool = False
    max_selections: Optional[int] = None
    min: Optional[float] = None
    max: Optional[float] = None
    distribution: str = "uniform"
    mean: Optional[float] = None
    stdev: Optional[float] = None
    topic: Optional[str] = None
    keywords: Optional[dict] = None
    allow_skip: bool = False
    skip_rate: float = 0.0

    @staticmethod
    def from_dict(d: dict) -> "Question":
        d = dict(d)
        d["type"] = QuestionType(d["type"])
        valid_keys = {f.name for f in fields(Question)}
        return Question(**{k: v for k, v in d.items() if k in valid_keys})


@dataclass
class Questionnaire:
    title: str
    questions: list
    description: str = ""

    @staticmethod
    def from_dict(d: dict) -> "Questionnaire":
        return Questionnaire(
            title=d.get("title", "Untitled Questionnaire"),
            description=d.get("description", ""),
            questions=[Question.from_dict(q) for q in d["questions"]],
        )

    @staticmethod
    def load(path: str) -> "Questionnaire":
        with open(path, "r", encoding="utf-8") as f:
            return Questionnaire.from_dict(json.load(f))


@dataclass
class Persona:
    id: int
    age: int
    age_group: str
    gender: str
    region: str
    sentiment: float  # latent overall disposition, 0..1 (drives correlated answers)
    engagement: float  # 0..1, affects text verbosity / answer detail
    tenure_years: float


@dataclass
class Response:
    persona_id: int
    answers: dict = field(default_factory=dict)
