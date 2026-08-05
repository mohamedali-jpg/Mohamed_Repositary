from __future__ import annotations

import os


def is_available() -> bool:
    """True if an Anthropic API key is set and the `anthropic` package is installed."""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return False
    try:
        import anthropic  # noqa: F401

        return True
    except ImportError:
        return False


def enhance_open_text(question_text: str, draft: str, topic: str = None) -> str:
    """Rewrite a template-generated draft answer into more natural phrasing.

    Kept as a thin, optional layer: the draft already encodes the persona's
    sentiment and topic, so the model is only asked to restyle it, not
    invent new content.
    """
    import anthropic

    client = anthropic.Anthropic()
    prompt = (
        "Rewrite the following short survey answer so it reads like a natural, "
        "off-the-cuff response from a real person, in 1-2 sentences. Keep the "
        "same sentiment and topic and do not introduce new facts.\n\n"
        f"Survey question: {question_text}\n"
        f"Draft answer: {draft}\n\n"
        "Rewritten answer:"
    )
    msg = client.messages.create(
        model="claude-sonnet-5",
        max_tokens=120,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text.strip()
