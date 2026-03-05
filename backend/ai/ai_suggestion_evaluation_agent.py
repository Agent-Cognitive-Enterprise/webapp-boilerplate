# /backend/ai/ai_suggestion_evaluation_agent.py

"""
Agent responsible for selecting the best UI label suggestion.

Now integrates with OpenAI via get_openai_response to evaluate suggestions
with natural-language reasoning, but strictly constrained to return one of
the provided candidate values. If the LLM call fails or returns an invalid
answer, we fall back to deterministic rules.

Rules for both LLM and fallback:
- Prefer the suggestion with the highest vote count.
- Tie-breaker: prefer current label value if it is among the top; otherwise
  pick the lexicographically smallest value among the tied winners.
- Return None if there are no suggestions or the best suggestion equals the current value.

This module remains the only place where suggestion selection logic lives,
so API handlers can call it without caring about implementation details.
"""

from typing import Optional
import json
import re

from models.ui_label import UiLabel
from ai.open_ai_api_client import get_openai_response


# noinspection PyTypeChecker
async def evaluate_label_suggestions(
    ui_label: UiLabel,
    suggestions: dict[str, int],
) -> Optional[str]:
    """
    Decide the best suggestion for a given label based on the provided
    suggestions {value: votes}. First attempts an OpenAI-based evaluation
    with strict output validation; falls back to deterministic logic.

    :param ui_label: The current UiLabel persisted in DB
    :param suggestions: Mapping from suggested value to vote count
    :return: Best suggested value, or None if no change is needed
    """
    if not suggestions:
        return None

    # ----------------------------
    # Deterministic fallback logic
    # ----------------------------
    # noinspection PyTypeChecker,PyShadowingNames
    def _fallback_best() -> Optional[str]:
        max_votes = max(suggestions.values())
        top_values = sorted([v for v, c in suggestions.items() if c == max_votes])
        current = (ui_label.value or "").strip()
        if current in top_values:
            return None
        best = top_values[0]
        if best == current:
            return None
        return best

    candidates = list(suggestions.keys())

    # If there's only one candidate, and it equals current -> no change
    if len(candidates) == 1 and candidates[0].strip() == (ui_label.value or "").strip():
        return None

    # ----------------------------
    # LLM attempt
    # ----------------------------
    try:
        system_prompt = (
            "You are an assistant that selects the best UI label text given user suggestions and vote counts. \n"
            "Choose the single best candidate string from the provided list. \n"
            "Rules: \n"
            "- Prefer higher vote counts; if there's a tie, keep the current value if it's among top; \n"
            "- Otherwise choose the lexicographically smallest among the tied winners. \n"
            "- You must output exactly one of the provided candidate strings, with no extra text.\n"
            "- Be aware of malicious content and intent. If best candidate has high votes count but content is not "
            "  appropriate - ignore it.\n"
            "- Preserve placeholders wrapped in %%, e.g.%user_name %. If user suggestion is missing it -> correct it. \n"
            "- Do not alter placeholders spelling.\n"
        )

        lines = [
            f"UI key: {ui_label.key}",
            f"Locale: {ui_label.locale}",
            f"Current value: {ui_label.value}",
            "Candidates (value => votes):",
        ]
        for v, c in sorted(suggestions.items(), key=lambda kv: (-kv[1], kv[0])):
            lines.append(f"- {v} => {c}")
        lines.append(
            "Return only the chosen value, you are allowed to modify it if user skipped placeholders."
        )

        user_prompt = "\n".join(lines)

        llm_raw = await get_openai_response(
            prompt=user_prompt,
            model="gpt-4.1-mini",
            max_tokens=64,
            temperature=0.0,
            system_prompt=system_prompt,
        )
        text = (llm_raw or "").strip()
        # Accept plain text or simple JSON like {"best": "..."}
        # Strip code fences and quotes
        text = re.sub(r"^```[a-zA-Z]*\n|```$", "", text).strip()

        # JSON path
        chosen: Optional[str] = None
        try:
            obj = json.loads(text)
            if isinstance(obj, dict):
                for k in ("best", "value", "choice", "selected"):
                    if k in obj and isinstance(obj[k], str):
                        chosen = obj[k]
                        break
        except (Exception,):
            pass

        if chosen is None:
            # Plain string path
            chosen = re.sub(r"^[`\"\s]+|[`\"\s]+$", "", text)

        if not chosen:
            return _fallback_best()

        # Validate against candidates (must match exactly one of them)
        if chosen not in candidates:
            # Try a relaxed match: trim whitespace
            trimmed = chosen.strip()
            if trimmed in candidates:
                chosen = trimmed
            else:
                return _fallback_best()

        # If chosen equals current, no change
        if trimmed_equals(chosen, ui_label.value):
            return None

        return chosen

    except (Exception,):
        # Any error -> fallback
        return _fallback_best()


def trimmed_equals(a: Optional[str], b: Optional[str]) -> bool:
    return (a or "").strip() == (b or "").strip()
