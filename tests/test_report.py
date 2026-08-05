from qsim.engine import simulate_responses
from qsim.models import Question, Questionnaire, QuestionType
from qsim.personas import generate_personas
from qsim.report import summarize


def test_summarize_nps_and_distribution():
    q = Questionnaire(
        title="T",
        questions=[
            Question(id="q1", type=QuestionType.NPS, text="Recommend?", sentiment_linked=True),
            Question(
                id="q2",
                type=QuestionType.SINGLE_CHOICE,
                text="Plan?",
                options=["Free", "Pro"],
                weights=[0.5, 0.5],
            ),
        ],
    )
    personas = generate_personas(200, seed=1)
    responses = simulate_responses(personas, q, seed=1)
    summary = summarize(q, responses)

    assert summary["n"] == 200
    assert "nps_score" in summary["questions"]["q1"]
    assert -100 <= summary["questions"]["q1"]["nps_score"] <= 100
    assert set(summary["questions"]["q2"]["distribution"].keys()).issubset({"Free", "Pro"})
    assert sum(summary["questions"]["q2"]["distribution"].values()) == 200
