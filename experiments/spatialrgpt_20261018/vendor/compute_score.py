"""Deterministic scorers used by the spatial_reasoning env reward."""

from __future__ import annotations

import json
import math
import re
from typing import Any, Optional


_SPATIALRGPT_NUMBER_RE = re.compile(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?")
_SPATIALRGPT_ANSWER_RE = re.compile(r"<answer>(.*?)(?:</answer>|$)", re.IGNORECASE | re.DOTALL)
_SPATIALRGPT_METRIC_RE = re.compile(
    r"([-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?)\s*"
    r"(millimeters?|millimetres?|mm|meters?|metres?|centimeters?|centimetres?|cm|inches?|inch|in|feet|foot|ft|m)\b",
    re.IGNORECASE,
)
_SPATIALRGPT_UNIT_FACTORS = {
    "m": 1.0,
    "meter": 1.0,
    "meters": 1.0,
    "metre": 1.0,
    "metres": 1.0,
    "cm": 0.01,
    "centimeter": 0.01,
    "centimeters": 0.01,
    "centimetre": 0.01,
    "centimetres": 0.01,
    "mm": 0.001,
    "millimeter": 0.001,
    "millimeters": 0.001,
    "millimetre": 0.001,
    "millimetres": 0.001,
    "in": 0.0254,
    "inch": 0.0254,
    "inches": 0.0254,
    "ft": 0.3048,
    "foot": 0.3048,
    "feet": 0.3048,
}


def extract_mindcube_final_answer(text: str) -> Optional[str]:
    """Extract the answer letter (A-E) from a model response. Prefers the last
    <answer>...</answer> block. Adapted from MindCube extractors."""
    if not text:
        return None

    answer_sections = re.findall(r"<answer>(.*?)(?:</answer>|<|$)", text, re.DOTALL | re.IGNORECASE)
    answer_sections = [s.strip() for s in answer_sections if s and s.strip()]
    if answer_sections:
        answer_section = answer_sections[-1]
        for pattern in [
            r"[Mm]y answer is ([A-E])",
            r"[Mm]y answer is ([A-E])\.",
            r"[Tt]he answer is ([A-E])",
            r"(?:Answer: )?([A-E])\.",
            r"\b([A-E])\b",
        ]:
            matches = list(re.finditer(pattern, answer_section))
            if matches:
                return matches[-1].group(1)

    simple = list(re.finditer(r"([A-E])\.", text))
    if simple:
        return simple[-1].group(1)

    patterns = [
        r'(?:Answer: )?([A-E])\. [A-Za-z0-9 \-\(\)\'",]+(?=(?:\n|$|\.|"))',
        r'(?:Answer: )?([A-E])\. [A-Za-z0-9 \-\(\)\'"]+',
        r"(?:^|\n)(?:Answer: )?([A-E])(?:\.|$|\s)",
        r"[\*\"]([A-E])[\*\"]",
        r"\bAnswer:?\s*([A-E])\b",
        r"[Mm]y answer is ([A-E])",
        r"[Mm]y answer is ([A-E])\.",
        r"answer is ([A-E])",
    ]
    for pattern in patterns:
        matches = list(re.finditer(pattern, text))
        if matches:
            return matches[-1].group(1)

    lines = text.split("\n")
    line_matches = []
    for i, line in enumerate(lines):
        m = re.search(r'([A-E])\. [A-Za-z0-9 \-\(\)\'",]+', line)
        if m:
            line_matches.append((i, m.group(1)))
    if line_matches:
        return line_matches[-1][1]

    for i in reversed(range(len(lines))):
        m = re.search(r"\b([A-E])\b", lines[i])
        if m:
            return m.group(1)
    return None


def _extract_answer_text(prediction: str) -> Optional[str]:
    m = re.search(r"<answer>(.*?)(?:</answer>|$)", prediction, re.DOTALL | re.IGNORECASE)
    if m:
        return m.group(1).strip()
    return None


def _parse_options_from_question(question: str) -> dict:
    """Map option letters to their (lowercased) text.

    Handles options that are newline-separated ("A. foo\nB. bar") AND inline on one
    line, as MindCube's binary yes/no items ship them ("A. No B. Yes"). Each option's
    text ends at the next option marker (letter + '.'/')' ), a newline, or end-of-string
    — the newline/marker terminator keeps a block that follows the options (e.g. an
    injected cognitive map) out of the last option's text. Used only as a fallback when
    letter extraction fails, so a free-text answer ("Yes") can still resolve to its
    letter via option-text match.
    """
    options = {}
    for match in re.finditer(r"([A-E])[.):\s]+(.+?)(?=\s[A-E][.)]\s|\n|$)", question):
        letter = match.group(1).upper()
        text = match.group(2).strip().rstrip(".").strip().lower()
        options[letter] = text
    return options


def compute_score_mindcube(prediction: str, ground_truth: str, question: Optional[str] = None) -> float:
    """1.0 if the extracted answer letter matches GT letter, else 0.0 (letter GT path)."""
    if prediction is None or len(str(prediction).strip()) == 0:
        return 0.0
    prediction_str = str(prediction)
    gt = str(ground_truth).strip()
    gt_is_letter = len(gt) == 1 and gt.upper() in "ABCDE"

    if gt_is_letter:
        extracted = extract_mindcube_final_answer(prediction_str)
        if extracted is None and question:
            answer_text = _extract_answer_text(prediction_str)
            if answer_text:
                atl = answer_text.lower().strip().rstrip(".")
                options = _parse_options_from_question(question)
                for letter, otext in options.items():
                    if atl == otext:
                        extracted = letter
                        break
                if extracted is None:
                    for letter, otext in options.items():
                        if atl in otext or otext in atl:
                            extracted = letter
                            break
        if extracted is None:
            return 0.0
        return 1.0 if extracted.upper() == gt.upper() else 0.0
    else:
        gt_lower = gt.lower().strip().rstrip(".")
        answer_text = _extract_answer_text(prediction_str)
        if answer_text:
            pred_lower = re.sub(r"^[A-E][.):\s]+", "", answer_text.lower().strip().rstrip(".")).strip()
            if pred_lower == gt_lower or pred_lower in gt_lower or gt_lower in pred_lower:
                return 1.0
        pred_lower = prediction_str.lower().strip()
        for pattern in [r"answer[:\s]+(.+)", r"(?:^|\n)([^\n]+)$"]:
            m = re.search(pattern, pred_lower, re.DOTALL)
            if m:
                candidate = m.group(1).strip().rstrip(".")
                if candidate == gt_lower or gt_lower in candidate:
                    return 1.0
        return 0.0


def compute_score_spatialrgpt(prediction: str, ground_truth: str, category: str) -> float:
    """Score released SpatialRGPT quantitative answers without an LLM judge."""
    try:
        gt = _parse_spatialrgpt_answer(ground_truth, category)
        pred = _parse_spatialrgpt_answer(prediction, category)
    except (TypeError, ValueError):
        return 0.0

    if category == "direction":
        hour_error = min(abs(int(gt) - int(pred)), 12 - abs(int(gt) - int(pred)))
        return 1.0 if hour_error <= 1 else 0.0
    return 1.0 if 0.75 * float(gt) <= float(pred) <= 1.25 * float(gt) else 0.0


def _parse_spatialrgpt_answer(text: str, category: str) -> float | int:
    payload = _spatialrgpt_answer_payload(text)
    parsed_json = _spatialrgpt_json(payload)
    if category == "direction":
        if isinstance(parsed_json, dict):
            for key in ("clock_hour", "hour", "value", "answer"):
                if key in parsed_json:
                    return _spatialrgpt_clock_hour(parsed_json[key])
        match = re.search(r"(\d{1,2})\s*(?:o[' ]?clock|clock)", payload, re.IGNORECASE)
        if match:
            return _spatialrgpt_clock_hour(match.group(1))
        numbers = _SPATIALRGPT_NUMBER_RE.findall(payload)
        if len(numbers) == 1:
            return _spatialrgpt_clock_hour(numbers[0])
        raise ValueError(f"could not parse clock direction from {text!r}")

    if isinstance(parsed_json, dict):
        value = next(
            (parsed_json[key] for key in ("value_m", "value", "answer") if key in parsed_json),
            None,
        )
        if value is not None:
            return _spatialrgpt_to_metres(value, str(parsed_json.get("unit", "m")))

    metric_match = _SPATIALRGPT_METRIC_RE.search(payload)
    if metric_match:
        return _spatialrgpt_to_metres(metric_match.group(1), metric_match.group(2))
    numbers = _SPATIALRGPT_NUMBER_RE.findall(
        re.sub(r"Region\s*\[\s*\d+\s*\]", "", payload, flags=re.IGNORECASE)
    )
    if len(numbers) != 1:
        raise ValueError(f"could not parse metric value from {text!r}")
    return _spatialrgpt_to_metres(numbers[0], "m")


def _spatialrgpt_answer_payload(text: str) -> str:
    raw = "" if text is None else str(text)
    matches = _SPATIALRGPT_ANSWER_RE.findall(raw)
    return (matches[-1] if matches else raw).strip()


def _spatialrgpt_json(text: str) -> Any:
    candidate = text.strip()
    if candidate.startswith("```"):
        candidate = re.sub(r"^```(?:json)?\s*|\s*```$", "", candidate, flags=re.IGNORECASE)
    start, end = candidate.find("{"), candidate.rfind("}")
    if start >= 0 and end > start:
        candidate = candidate[start : end + 1]
    try:
        return json.loads(candidate)
    except (json.JSONDecodeError, TypeError):
        return None


def _spatialrgpt_to_metres(value: Any, unit: str) -> float:
    number = float(value)
    factor = _SPATIALRGPT_UNIT_FACTORS.get(unit.strip().lower().rstrip("."))
    if factor is None or not math.isfinite(number) or number < 0:
        raise ValueError(f"invalid metric answer value={value!r}, unit={unit!r}")
    return number * factor


def _spatialrgpt_clock_hour(value: Any) -> int:
    number = float(value)
    if not math.isfinite(number) or not number.is_integer():
        raise ValueError(f"clock hour must be an integer, got {value!r}")
    hour = int(number)
    if hour == 0:
        hour = 12
    if not 1 <= hour <= 12:
        raise ValueError(f"clock hour must be in [1, 12], got {value!r}")
    return hour


def compute_score(data_source: str, solution_str: str, ground_truth: str, *, task_type: str = "binary", scene: Optional[str] = None, question: Optional[str] = None) -> float:
    """Dispatch to the deterministic scorer for the record's data source."""
    if data_source == "spatialrgpt":
        return compute_score_spatialrgpt(solution_str, ground_truth, task_type)
    return compute_score_mindcube(solution_str, ground_truth, question=question)
