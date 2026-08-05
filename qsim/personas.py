from __future__ import annotations

import random
from typing import Optional

from .models import Persona

AGE_GROUPS = [
    ("18-24", 18, 24),
    ("25-34", 25, 34),
    ("35-44", 35, 44),
    ("45-54", 45, 54),
    ("55-64", 55, 64),
    ("65+", 65, 80),
]
AGE_GROUP_WEIGHTS = [0.14, 0.24, 0.22, 0.18, 0.14, 0.08]

GENDERS = ["Female", "Male", "Non-binary"]
GENDER_WEIGHTS = [0.49, 0.48, 0.03]

REGIONS = ["North America", "Europe", "Asia-Pacific", "Africa", "Latin America", "Middle East"]
REGION_WEIGHTS = [0.28, 0.26, 0.24, 0.09, 0.09, 0.04]


def _beta_trait(rng: random.Random, mean: float, spread: float = 6.0) -> float:
    """Sample a 0..1 trait from a Beta distribution with a given target mean.

    Beta gives a bounded, realistically-shaped distribution (more mass near
    the mean, tapering at the extremes) instead of a flat uniform draw.
    """
    mean = min(max(mean, 0.01), 0.99)
    a = mean * spread
    b = (1 - mean) * spread
    return rng.betavariate(a, b)


def generate_personas(
    n: int,
    seed: Optional[int] = None,
    mean_sentiment: float = 0.62,
) -> list:
    """Generate n synthetic respondents with demographic + latent-disposition traits.

    `sentiment` is the key latent trait: it's what makes a single persona's
    answers cohere across related questions (a happy respondent tends to give
    happy answers everywhere) rather than every question being independent noise.
    """
    rng = random.Random(seed)
    personas = []
    for i in range(1, n + 1):
        group, lo, hi = rng.choices(AGE_GROUPS, weights=AGE_GROUP_WEIGHTS, k=1)[0]
        age = rng.randint(lo, hi)
        gender = rng.choices(GENDERS, weights=GENDER_WEIGHTS, k=1)[0]
        region = rng.choices(REGIONS, weights=REGION_WEIGHTS, k=1)[0]
        sentiment = _beta_trait(rng, mean=mean_sentiment)
        engagement = _beta_trait(rng, mean=0.55, spread=5.0)
        tenure = max(0.0, rng.gauss(3.0, 2.2))
        personas.append(
            Persona(
                id=i,
                age=age,
                age_group=group,
                gender=gender,
                region=region,
                sentiment=sentiment,
                engagement=engagement,
                tenure_years=round(tenure, 1),
            )
        )
    return personas
