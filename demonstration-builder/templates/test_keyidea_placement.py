"""Guard the locked "Key Idea placement" rule across every demonstration.

The rule (see the demonstration-builder skill, PATTERN.md section 7): the per-example
"Key Idea" and the right-column diagram are separate regions and never share space.
Which one holds the right column is decided per example by the ``diagram:`` flag:

- ``diagram: true``  -> the diagram owns the right column, so the Key Idea must be a
                        fold-out **button** (a separate ``concept:`` block).
- ``diagram: false`` -> there is no diagram, so the Key Idea fills the right column as
                        an **aside** (the ``concept:`` argument written *on the topic*).

Two ways to break the rule, both of which this test rejects:

1. A ``concept:`` *button block* together with ``diagram: false`` — that paints a Key
   Idea button next to an empty right column.
2. A ``concept:`` *argument on a ``diagram: true`` topic* — the engine silently drops it
   because the diagram already owns the right column.

This file is self-contained (no engine imports) so it can be copied verbatim into any
demonstration project's test set.
"""

from __future__ import annotations

from pathlib import Path

import yaml
import pytest


# ---------------------------------------------------------------------------
# The check
# ---------------------------------------------------------------------------


def keyidea_violations(demo: dict) -> list[str]:
    """Return a list of human-readable rule violations for one parsed demo file.

    Args:
        demo: A demo YAML file already parsed into a dict. The only key that matters
            is ``blocks`` — the ordered list of content blocks. Each block is a
            one-key dict such as ``{"concept": {...}}`` or ``{"topic": {...}}``.

    Returns:
        One message per violation found. An empty list means the demo obeys the rule.
    """
    blocks = demo.get("blocks", []) or []

    # Is there a stand-alone Key Idea *button* block anywhere in this demo?
    has_concept_button = any(isinstance(b, dict) and "concept" in b for b in blocks)

    # Every ``topic`` block, with its diagram flag and any inline concept argument.
    topics = [b["topic"] for b in blocks if isinstance(b, dict) and "topic" in b]

    problems: list[str] = []
    for topic in topics:
        # ``diagram:`` defaults to true when the author omits it.
        has_diagram = topic.get("diagram", True)
        has_concept_arg = "concept" in topic
        topic_id = topic.get("id", "<unnamed>")

        if not has_diagram and has_concept_button:
            problems.append(
                f"topic '{topic_id}' has diagram:false but the demo also has a "
                f"stand-alone concept button block — that leaves an empty right column. "
                f"Put the Key Idea on the topic (concept:) as the aside instead."
            )
        if has_diagram and has_concept_arg:
            problems.append(
                f"topic '{topic_id}' is diagram:true yet carries a concept: argument, "
                f"which the engine ignores. Move the Key Idea to a separate concept "
                f"button block."
            )
    return problems


# ---------------------------------------------------------------------------
# Unit cases — synthetic demos, both legal and illegal (the red/green proof)
# ---------------------------------------------------------------------------

_LEGAL = {
    "no-diagram -> concept aside on the topic": {
        "blocks": [{"topic": {"id": "t", "source": "t", "diagram": False,
                              "concept": "${t.explanation}"}}],
    },
    "diagram -> concept as a button block": {
        "blocks": [
            {"concept": {"id": "c", "text": "${t.explanation}"}},
            {"topic": {"id": "t", "source": "t", "diagram": True}},
        ],
    },
}

_ILLEGAL = {
    "button block + diagram:false (empty right column)": {
        "blocks": [
            {"concept": {"id": "c", "text": "x"}},
            {"topic": {"id": "t", "source": "t", "diagram": False}},
        ],
    },
    "concept arg on an explicit diagram:true topic": {
        "blocks": [{"topic": {"id": "t", "source": "t", "diagram": True,
                              "concept": "x"}}],
    },
    "concept arg on a default (diagram omitted -> true) topic": {
        "blocks": [{"topic": {"id": "t", "source": "t", "concept": "x"}}],
    },
}


@pytest.mark.parametrize("name", list(_LEGAL), ids=list(_LEGAL))
def test_legal_demos_have_no_violations(name: str) -> None:
    """Every well-formed pairing must report zero violations."""
    assert keyidea_violations(_LEGAL[name]) == []


@pytest.mark.parametrize("name", list(_ILLEGAL), ids=list(_ILLEGAL))
def test_illegal_demos_are_caught(name: str) -> None:
    """Every rule-breaking pairing must be reported."""
    assert keyidea_violations(_ILLEGAL[name]), f"expected a violation for: {name}"


# ---------------------------------------------------------------------------
# Real demos — no shipped demonstration may break the rule
# ---------------------------------------------------------------------------

# cpp_labs/tests/this_file  ->  parents[2] is the project root.
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_DEMO_FILES = sorted(_PROJECT_ROOT.glob("cpp_labs/*/demos/*.demo.yaml"))


@pytest.mark.parametrize(
    "demo_path", _DEMO_FILES, ids=[p.name for p in _DEMO_FILES]
)
def test_shipped_demos_follow_the_rule(demo_path: Path) -> None:
    """Scan every real demo file and fail the build on any placement violation."""
    demo = yaml.safe_load(demo_path.read_text())
    problems = keyidea_violations(demo)
    assert not problems, f"{demo_path.name}: " + "; ".join(problems)
