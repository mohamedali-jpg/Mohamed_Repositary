from __future__ import annotations

import argparse
import json
import os

from .engine import simulate_responses
from .export import responses_to_rows, write_csv, write_json
from .models import Questionnaire, QuestionType
from .personas import generate_personas
from .report import format_summary_text, summarize


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description="Simulate N respondents answering a questionnaire.")
    parser.add_argument("questionnaire", help="Path to a questionnaire JSON file")
    parser.add_argument("-n", "--num-respondents", type=int, default=200)
    parser.add_argument("-o", "--output-dir", default="output")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for reproducible runs")
    parser.add_argument(
        "--mean-sentiment",
        type=float,
        default=0.62,
        help="Target average latent satisfaction (0-1) across the simulated population",
    )
    parser.add_argument(
        "--llm",
        action="store_true",
        help="Use the Claude API to naturalize open-text answers (requires ANTHROPIC_API_KEY)",
    )
    args = parser.parse_args(argv)

    questionnaire = Questionnaire.load(args.questionnaire)
    personas = generate_personas(args.num_respondents, seed=args.seed, mean_sentiment=args.mean_sentiment)
    responses = simulate_responses(personas, questionnaire, seed=args.seed)

    if args.llm:
        from . import llm

        if llm.is_available():
            for q in questionnaire.questions:
                if q.type == QuestionType.OPEN_TEXT:
                    for r in responses:
                        draft = r.answers.get(q.id)
                        if draft:
                            r.answers[q.id] = llm.enhance_open_text(q.text, draft, q.topic)
        else:
            print(
                "Warning: --llm requested but ANTHROPIC_API_KEY or the 'anthropic' package "
                "is not available; using template-based text instead."
            )

    os.makedirs(args.output_dir, exist_ok=True)

    rows = responses_to_rows(questionnaire, personas, responses)
    write_csv(os.path.join(args.output_dir, "responses.csv"), rows)
    write_json(os.path.join(args.output_dir, "responses.json"), questionnaire, personas, responses)

    summary = summarize(questionnaire, responses)
    summary_text = format_summary_text(summary)
    with open(os.path.join(args.output_dir, "summary.txt"), "w", encoding="utf-8") as f:
        f.write(summary_text)
    with open(os.path.join(args.output_dir, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"Simulated {len(responses)} responses for '{questionnaire.title}'")
    print(f"Wrote: {args.output_dir}/responses.csv, responses.json, summary.txt, summary.json")
    print()
    print(summary_text)


if __name__ == "__main__":
    main()
