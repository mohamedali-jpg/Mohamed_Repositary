from qsim.personas import generate_personas


def test_generate_personas_count_and_seed_reproducibility():
    a = generate_personas(200, seed=42)
    b = generate_personas(200, seed=42)
    assert len(a) == 200
    assert [p.__dict__ for p in a] == [p.__dict__ for p in b]


def test_persona_fields_in_range():
    personas = generate_personas(50, seed=1)
    for p in personas:
        assert 18 <= p.age <= 80
        assert 0.0 <= p.sentiment <= 1.0
        assert 0.0 <= p.engagement <= 1.0
        assert p.tenure_years >= 0


def test_mean_sentiment_shifts_population():
    low = generate_personas(300, seed=9, mean_sentiment=0.2)
    high = generate_personas(300, seed=9, mean_sentiment=0.85)
    avg_low = sum(p.sentiment for p in low) / len(low)
    avg_high = sum(p.sentiment for p in high) / len(high)
    assert avg_low < 0.35
    assert avg_high > 0.65
