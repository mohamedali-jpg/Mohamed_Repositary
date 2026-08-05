from __future__ import annotations

import random
from typing import Optional

from .models import Persona, Question, QuestionType, Response, Questionnaire
from .templates import generate_open_text


def _clip(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def _likert_value(rng: random.Random, sentiment: float, scale: int, noise: float = 0.16) -> int:
    val = _clip(sentiment + rng.gauss(0, noise), 0.0, 1.0)
    return int(round(1 + val * (scale - 1)))


def _nps_value(rng: random.Random, sentiment: float, noise: float = 0.18) -> int:
    val = _clip(sentiment + rng.gauss(0, noise), 0.0, 1.0)
    return int(round(val * 10))


def _weighted_choice(rng: random.Random, options: list, weights: Optional[list] = None):
    if weights is None:
        weights = [1] * len(options)
    return rng.choices(options, weights=weights, k=1)[0]


def _sentiment_biased_weights(options: list, weights: Optional[list], sentiment: float) -> list:
    """Skew weights toward the end of `options` as sentiment rises.

    Assumes options are ordered least -> most positive when a question is
    marked sentiment_linked (e.g. ["Very dissatisfied", ..., "Very satisfied"]).
    """
    n = len(options)
    weights = list(weights) if weights else [1.0] * n
    biased = []
    for idx, w in enumerate(weights):
        pos = idx / max(1, n - 1)
        skew = 1.0 + 2.5 * (1 - abs(pos - sentiment))
        biased.append(w * skew)
    return biased


def _multi_choice(rng: random.Random, options: list, weights: Optional[list], max_selections: Optional[int]) -> list:
    k = max_selections or len(options)
    k = min(k, len(options))
    n_pick = rng.randint(1, k)
    pool = list(options)
    w = list(weights) if weights else [1.0] * len(pool)
    picks = []
    for _ in range(n_pick):
        if not pool:
            break
        chosen = rng.choices(pool, weights=w, k=1)[0]
        idx = pool.index(chosen)
        picks.append(pool.pop(idx))
        w.pop(idx)
    return picks


def _numeric_value(rng: random.Random, q: Question) -> float:
    lo = q.min if q.min is not None else 0
    hi = q.max if q.max is not None else 100
    if q.distribution == "normal":
        mean = q.mean if q.mean is not None else (lo + hi) / 2
        stdev = q.stdev if q.stdev is not None else (hi - lo) / 6
        val = rng.gauss(mean, stdev)
    else:
        val = rng.uniform(lo, hi)
    return round(_clip(val, lo, hi), 1)


def answer_question(rng: random.Random, persona: Persona, q: Question):
    if q.allow_skip and rng.random() < q.skip_rate:
        return None

    if q.type == QuestionType.LIKERT:
        return _likert_value(rng, persona.sentiment, q.scale)

    if q.type == QuestionType.NPS:
        return _nps_value(rng, persona.sentiment)

    if q.type == QuestionType.YES_NO:
        options = q.options or ["Yes", "No"]
        weights = q.weights
        if q.sentiment_linked:
            weights = _sentiment_biased_weights(options, weights, persona.sentiment)
        return _weighted_choice(rng, options, weights)

    if q.type == QuestionType.SINGLE_CHOICE:
        weights = q.weights
        if q.sentiment_linked:
            weights = _sentiment_biased_weights(q.options, weights, persona.sentiment)
        return _weighted_choice(rng, q.options, weights)

    if q.type == QuestionType.MULTI_CHOICE:
        return _multi_choice(rng, q.options, q.weights, q.max_selections)

    if q.type == QuestionType.NUMERIC:
        return _numeric_value(rng, q)

    if q.type == QuestionType.OPEN_TEXT:
        return generate_open_text(rng, persona, q)

    raise ValueError(f"Unsupported question type: {q.type}")


def simulate_responses(personas: list, questionnaire: Questionnaire, seed: Optional[int] = None) -> list:
    rng = random.Random(seed)
    responses = []
    for persona in personas:
        answers = {}
        for q in questionnaire.questions:
            answers[q.id] = answer_question(rng, persona, q)
        responses.append(Response(persona_id=persona.id, answers=answers))
    return responses
