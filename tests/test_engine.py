from qsim.engine import simulate_responses
from qsim.models import Question, Questionnaire, QuestionType
from qsim.personas import generate_personas


def _sample_questionnaire():
    return Questionnaire(
        title="Test",
        questions=[
            Question(id="q1", type=QuestionType.LIKERT, text="Satisfaction?", scale=5, sentiment_linked=True),
            Question(id="q2", type=QuestionType.SINGLE_CHOICE, text="Color?", options=["Red", "Blue", "Green"]),
            Question(
                id="q3",
                type=QuestionType.MULTI_CHOICE,
                text="Features?",
                options=["A", "B", "C", "D"],
                max_selections=2,
            ),
            Question(id="q4", type=QuestionType.NUMERIC, text="Score?", min=0, max=10, distribution="uniform"),
            Question(
                id="q5",
                type=QuestionType.OPEN_TEXT,
                text="Comments?",
                topic="service",
                keywords={
                    "positive": ["great support"],
                    "negative": ["slow replies"],
                    "neutral": ["more docs"],
                },
            ),
            Question(id="q6", type=QuestionType.NPS, text="Recommend?", sentiment_linked=True),
            Question(id="q7", type=QuestionType.YES_NO, text="Contacted support?"),
        ],
    )


def test_simulate_responses_count_and_reproducibility():
    q = _sample_questionnaire()
    personas = generate_personas(200, seed=7)
    r1 = simulate_responses(personas, q, seed=123)
    r2 = simulate_responses(personas, q, seed=123)
    assert len(r1) == 200
    assert [r.answers for r in r1] == [r.answers for r in r2]


def test_answers_within_valid_ranges():
    q = _sample_questionnaire()
    personas = generate_personas(200, seed=7)
    responses = simulate_responses(personas, q, seed=1)
    for r in responses:
        assert 1 <= r.answers["q1"] <= 5
        assert r.answers["q2"] in ["Red", "Blue", "Green"]
        assert set(r.answers["q3"]).issubset({"A", "B", "C", "D"})
        assert 1 <= len(r.answers["q3"]) <= 2
        assert 0 <= r.answers["q4"] <= 10
        assert isinstance(r.answers["q5"], str) and len(r.answers["q5"]) > 0
        assert 0 <= r.answers["q6"] <= 10
        assert r.answers["q7"] in ["Yes", "No"]


def test_sentiment_linked_questions_correlate_with_persona_sentiment():
    q = _sample_questionnaire()
    high = generate_personas(300, seed=7, mean_sentiment=0.9)
    low = generate_personas(300, seed=7, mean_sentiment=0.1)
    r_high = simulate_responses(high, q, seed=5)
    r_low = simulate_responses(low, q, seed=5)
    avg_high = sum(r.answers["q1"] for r in r_high) / len(r_high)
    avg_low = sum(r.answers["q1"] for r in r_low) / len(r_low)
    assert avg_high > avg_low


def test_skip_logic_produces_none():
    q = Questionnaire(
        title="Skip test",
        questions=[
            Question(id="q1", type=QuestionType.OPEN_TEXT, text="Feedback?", allow_skip=True, skip_rate=1.0),
        ],
    )
    personas = generate_personas(20, seed=1)
    responses = simulate_responses(personas, q, seed=1)
    assert all(r.answers["q1"] is None for r in responses)
