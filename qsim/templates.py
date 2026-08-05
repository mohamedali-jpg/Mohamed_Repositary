from __future__ import annotations

import random

from .models import Persona, Question

_SENTIMENT_OPENERS = {
    "very_positive": ["Honestly, I love it.", "Really happy with this.", "This has been great."],
    "positive": ["Overall it's good.", "Pretty satisfied so far.", "It works well for me."],
    "neutral": ["It's okay.", "Nothing special either way.", "Mixed feelings, honestly."],
    "negative": ["I'm a bit disappointed.", "It hasn't quite met expectations.", "There's room for improvement."],
    "very_negative": ["I'm frustrated with this.", "This really needs work.", "Not a great experience."],
}


def _bucket(sentiment: float) -> str:
    if sentiment >= 0.85:
        return "very_positive"
    if sentiment >= 0.6:
        return "positive"
    if sentiment >= 0.4:
        return "neutral"
    if sentiment >= 0.2:
        return "negative"
    return "very_negative"


def generate_open_text(rng: random.Random, persona: Persona, q: Question) -> str:
    """Template-based free-text answer whose tone tracks the persona's sentiment.

    This is the no-API-key default. See qsim/llm.py for an optional pass that
    rewrites these drafts into more natural phrasing via the Claude API.
    """
    bucket = _bucket(persona.sentiment)
    opener = rng.choice(_SENTIMENT_OPENERS[bucket])

    keywords = q.keywords or {}
    pool_key = (
        "positive" if bucket in ("very_positive", "positive")
        else "negative" if bucket in ("negative", "very_negative")
        else "neutral"
    )
    pool = keywords.get(pool_key) or keywords.get("neutral") or []

    if pool:
        detail = rng.choice(pool)
        if pool_key == "negative":
            body = f"One thing that could be better is {detail}."
        elif pool_key == "positive":
            body = f"I'd just say: {detail}."
        else:
            body = f"Maybe consider {detail}."
    else:
        topic = q.topic or "this"
        body = f"Not much else to add about {topic} right now."

    text = f"{opener} {body}"

    if persona.engagement > 0.7:
        extra_pool = keywords.get("neutral") or []
        if extra_pool:
            text += f" Also, {rng.choice(extra_pool)} would help."

    return text
