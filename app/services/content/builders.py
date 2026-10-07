"""Small helpers that turn compact content definitions into the client/server exam structure.

A section (Listening part or Reading passage) holds `groups`. Each group is one block of
instructions as printed on a real paper ("Questions 1-10 ... Write ONE WORD ONLY") plus its
questions. Gap questions mark the answer position with `____`.
"""

from __future__ import annotations

from typing import Any

TFNG = [
    {"value": "TRUE", "label": "TRUE"},
    {"value": "FALSE", "label": "FALSE"},
    {"value": "NOT GIVEN", "label": "NOT GIVEN"},
]
YNNG = [
    {"value": "YES", "label": "YES"},
    {"value": "NO", "label": "NO"},
    {"value": "NOT GIVEN", "label": "NOT GIVEN"},
]


def lettered(labels: list[str], *, roman: bool = False) -> list[dict[str, str]]:
    """Turn ['text a', 'text b'] into [{'value': 'A', 'label': 'text a'}, ...] (or i, ii, iii...)."""
    romans = ["i", "ii", "iii", "iv", "v", "vi", "vii", "viii", "ix", "x"]
    keys = romans if roman else [chr(ord("A") + i) for i in range(len(labels))]
    return [{"value": keys[i], "label": text} for i, text in enumerate(labels)]


def gap(number: int, prompt: str) -> dict[str, Any]:
    return {"number": number, "prompt": prompt}


def mcq(number: int, prompt: str, options: list[str]) -> dict[str, Any]:
    return {"number": number, "prompt": prompt, "options": lettered(options)}


def item(number: int, prompt: str) -> dict[str, Any]:
    """A question whose options come from the group's shared box (matching / TFNG / YNNG)."""
    return {"number": number, "prompt": prompt}


def group(
    kind: str,
    instructions: str,
    questions: list[dict[str, Any]],
    *,
    title: str | None = None,
    box: list[dict[str, str]] | None = None,
    box_title: str | None = None,
    figure_svg: str | None = None,
    table: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """kind: 'gap' | 'mcq' | 'matching' | 'tfng' | 'ynng' | 'multi'.

    - 'multi' = "Choose TWO letters": the group's questions share one prompt and the `box` options;
      answers are order-independent (the client stores the chosen letters sorted, the key is sorted).
    - `table` = {"columns": [...], "rows": [[cell, ...], ...]} for table completion; a cell marks a
      gap with [[n]] where n is the question number.
    """
    if kind == "tfng":
        box = TFNG
    elif kind == "ynng":
        box = YNNG
    numbers = [q["number"] for q in questions]
    out: dict[str, Any] = {
        "kind": kind,
        "range": f"{min(numbers)}–{max(numbers)}" if len(numbers) > 1 else str(numbers[0]),
        "instructions": instructions,
        "questions": questions,
    }
    if title:
        out["title"] = title
    if box:
        out["box"] = box
    if box_title:
        out["box_title"] = box_title
    if figure_svg:
        out["figure_svg"] = figure_svg
    if table:
        out["table"] = table
    return out


def flatten_questions(sections: list[dict[str, Any]], section_key: str) -> list[dict[str, Any]]:
    """Produce the flat 1..40 question list (kept for scoring/navigation and backwards compatibility)."""
    flat: list[dict[str, Any]] = []
    for section in sections:
        for g_idx, grp in enumerate(section["groups"]):
            for q in grp["questions"]:
                options = q.get("options") or grp.get("box")
                entry: dict[str, Any] = {
                    "id": str(q["number"]),
                    "number": q["number"],
                    section_key: section["number"],
                    "group": g_idx,
                    "type": grp["kind"],
                    "prompt": q["prompt"],
                }
                if options:
                    entry["options"] = options
                flat.append(entry)
    flat.sort(key=lambda e: e["number"])
    return flat
