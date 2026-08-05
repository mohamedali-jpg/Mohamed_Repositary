# Questionnaire Response Simulator

Simulates a population of respondents (default: 200) answering any
questionnaire you define in JSON, and exports the results as CSV, JSON,
and a summary report — as if that many real people had taken the survey.

## Why not just random-per-question?

Rolling independent random numbers for every question, for every
respondent, produces noise, not people: an individual's satisfaction
score and their NPS score and their "would you recommend" answer would
be totally uncorrelated, which no real respondent looks like.

Instead, each simulated respondent is a **persona**: a set of
demographic attributes (age, gender, region, tenure) plus a latent
`sentiment` trait (0-1) representing their overall disposition. Any
question marked `sentiment_linked` draws its answer from that persona's
sentiment (with noise), so one respondent's answers cohere across
related questions the way a real person's would.

## Quick start

```bash
pip install -r requirements.txt   # only needed for tests / --llm mode
python -m qsim.cli examples/customer_satisfaction.json -n 200 --seed 42
```

This writes to `output/`:
- `responses.csv` — one row per respondent
- `responses.json` — full structured output (respondent attributes + answers)
- `summary.txt` / `summary.json` — aggregate stats per question (means, distributions, NPS score, sample open-text answers)

Or install it as a CLI:

```bash
pip install -e .
qsim examples/customer_satisfaction.json -n 200 --seed 42
```

## Defining a questionnaire

Questionnaires are JSON files with a list of questions. Supported types:

| type            | fields                                                | notes |
|-----------------|--------------------------------------------------------|-------|
| `likert`        | `scale` (default 5), `sentiment_linked`                | e.g. 1-5 agreement scale |
| `nps`           | `sentiment_linked`                                      | 0-10 "how likely to recommend" |
| `single_choice` | `options`, `weights`, `sentiment_linked`                | one answer |
| `multi_choice`  | `options`, `weights`, `max_selections`                  | select-all-that-apply |
| `yes_no`        | `options` (default `["Yes","No"]`), `weights`, `sentiment_linked` | |
| `numeric`       | `min`, `max`, `distribution` (`uniform`/`normal`), `mean`, `stdev` | |
| `open_text`     | `topic`, `keywords: {positive, negative, neutral}`      | template-based free text, sentiment-toned |

Every question also accepts `allow_skip` + `skip_rate` (0-1) to simulate
non-response, common on open-text questions.

For `sentiment_linked` questions with explicit `options`, list them from
least to most positive (e.g. `["Very dissatisfied", ..., "Very satisfied"]`)
— the bias logic assumes that ordering.

See `examples/customer_satisfaction.json` for a complete example covering
every question type.

## Architecture

- `qsim/models.py` — `Question`, `Questionnaire`, `Persona`, `Response` data types
- `qsim/personas.py` — generates the synthetic population (demographics + latent sentiment/engagement traits)
- `qsim/engine.py` — answers each question per persona (weighted choice, sentiment-biased choice, likert/NPS mapping, numeric sampling)
- `qsim/templates.py` — sentiment-toned template generation for open-text answers
- `qsim/llm.py` — optional: rewrites template drafts via the Claude API for more natural phrasing (`--llm`, requires `ANTHROPIC_API_KEY`)
- `qsim/report.py` — aggregate statistics (means, distributions, NPS score) and a human-readable summary
- `qsim/export.py` — CSV/JSON writers
- `qsim/cli.py` — command-line entry point

## Reproducibility

Pass `--seed N` to get identical output across runs (same personas, same
answers). Omit it for a fresh random population each time.

## Tuning the population

`--mean-sentiment` (0-1, default 0.62) shifts the whole simulated
population's disposition — useful for testing how a survey's aggregate
results would look under a more or less satisfied customer base.

## Optional: LLM-naturalized open text

By default, open-text answers come from lightweight templates (fast, free,
no dependencies). Pass `--llm` with `ANTHROPIC_API_KEY` set and the
`anthropic` package installed to have Claude rewrite each draft into more
natural phrasing (same sentiment/topic, no new facts). This makes one API
call per open-text answer per respondent, so it's slower and has a cost —
use it when text realism matters more than speed.

## Tests

```bash
pip install -r requirements.txt
pytest
```
