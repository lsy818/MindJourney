"""Strict multiple-choice answer parsing for benchmark evaluation.

The released MindJourney scorer used substring matching, which is ambiguous for
benchmarks whose options overlap.  This module prefers benchmark-provided
choice labels and falls back to an exact, normalized option-text match.
"""

from __future__ import annotations

import re
from typing import Iterable, Optional


_LEADING_LABEL = re.compile(r"^\s*([A-Z])\s*[\.:\)]\s*(.*?)\s*$", re.DOTALL)


def _normalized_text(value: str) -> str:
    return " ".join(str(value).strip().casefold().split())


def _choice_label(choice: str, index: int) -> str:
    match = _LEADING_LABEL.match(str(choice))
    return match.group(1) if match else chr(ord("A") + index)


def _choice_body(choice: str) -> str:
    match = _LEADING_LABEL.match(str(choice))
    return match.group(2) if match else str(choice).strip()


def extract_answer_label(response: str, answer_choices: Iterable[str]) -> Optional[str]:
    """Return one unambiguous A-Z label from the model's final answer.

    Only the final non-empty line is considered, matching the released prompt's
    instruction that the last line contain the answer.  Labels must be explicit
    or the line must exactly match one unique option (with whitespace folded).
    """

    choices = list(answer_choices)
    if not response or not choices:
        return None
    labels = [_choice_label(choice, index) for index, choice in enumerate(choices)]
    valid = set(labels)
    lines = [line.strip() for line in str(response).splitlines() if line.strip()]
    if not lines:
        return None
    final_line = lines[-1]
    boxed = re.fullmatch(r"\\boxed\{\s*([A-Z])\s*\}", final_line, flags=re.I)
    if boxed:
        label = boxed.group(1).upper()
        return label if label in valid else None
    final_line = re.sub(
        r"^\s*(?:the\s+)?(?:final\s+)?answer\s*(?::|is)\s*",
        "",
        final_line,
        flags=re.I,
    )
    final_line = re.sub(r"^\*\*(.*?)\*\*$", r"\1", final_line).strip()

    explicit = re.fullmatch(
        r"\s*(?:option\s*)?[\(\[]?([A-Z])[\)\]]?[\.:]?\s*",
        final_line,
        flags=re.I,
    )
    if explicit:
        label = explicit.group(1).upper()
        return label if label in valid else None

    normalized = _normalized_text(final_line)
    matches = []
    for label, choice in zip(labels, choices):
        if normalized in {
            _normalized_text(choice),
            _normalized_text(_choice_body(choice)),
        }:
            matches.append(label)
    return matches[0] if len(set(matches)) == 1 else None


def score_multiple_choice_response(response: str, question: dict) -> str:
    """Return ``correct``, ``wrong``, or ``out of control`` for one response."""

    choices = list(question["answer_choices"])
    predicted = extract_answer_label(response, choices)
    if predicted is None:
        return "out of control"

    expected = question.get("correct_answer_letter") or question.get(
        "correct_answer_label"
    )
    if expected is None:
        correct = str(question["correct_answer"])
        for index, choice in enumerate(choices):
            if _normalized_text(correct) in {
                _normalized_text(choice),
                _normalized_text(_choice_body(choice)),
            }:
                expected = _choice_label(choice, index)
                break
    if expected is None:
        return "out of control"
    return "correct" if predicted == str(expected).strip().upper() else "wrong"
