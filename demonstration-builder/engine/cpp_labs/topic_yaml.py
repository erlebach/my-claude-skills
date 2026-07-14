"""Load a subject's topic definitions from YAML into TopicTemplate objects.

Shared across subjects: the source of truth for each topic's C++ template,
controls, and sub-cases is a ``<subject>/topics/<id>.topic.yaml`` file. This
loader is the only place that knows the YAML shape; each subject's ``topics.py``
is a thin re-export shim that calls :func:`load_topics` with its own topics dir.
"""
from __future__ import annotations

import re
from pathlib import Path

import yaml

from cpp_labs.code_generator import CaseDef, ControlDef, TopicTemplate

_REQUIRED = ("id", "name", "template", "explanation", "group")


def _control(d: dict) -> ControlDef:
    return ControlDef(
        id=d["id"],
        label=d["label"],
        kind=d["kind"],
        options=list(d.get("options", [])),
        default=d.get("default", ""),
        placeholder=d.get("placeholder", ""),
        value_map=d.get("value_map"),
    )


def _case(d: dict) -> CaseDef:
    return CaseDef(label=d["label"], subs=dict(d.get("subs", {})))


def _flag_variant(d: dict) -> dict:
    """Normalize one flag_variants entry to {"label", "flags"}.

    ``flags`` is required; ``label`` defaults to the flags joined by a space so
    a topic can write ``- flags: ["-O2"]`` and get a ``-O2`` tab for free.
    """
    flags = list(d["flags"])
    return {"label": d.get("label") or " ".join(flags), "flags": flags}


_PC_REQUIRED_GROUPS = {"bar": ("label", "y"), "line": ("x", "y"), "scatter": ("x", "y")}


def _validate_perf_chart(block: dict, topic_id: str) -> dict:
    """Validate a perf_chart: block; raise ValueError on authoring mistakes."""
    for chart_id, spec in block.items():
        mode = spec.get("mode", "bar")
        if mode not in _PC_REQUIRED_GROUPS:
            raise ValueError(
                f"topic {topic_id!r} perf_chart {chart_id!r}: mode must be "
                f"'bar', 'line', or 'scatter', got {mode!r}")
        src = spec.get("from")
        if src and src not in ("variants", "flag_variants"):
            raise ValueError(
                f"topic {topic_id!r} perf_chart {chart_id!r}: from must be "
                f"'variants' or 'flag_variants', got {src!r}")
        if "match" not in spec:
            raise ValueError(
                f"topic {topic_id!r} perf_chart {chart_id!r}: missing 'match' regex")
        try:
            groups = re.compile(spec["match"]).groupindex
        except re.error as exc:
            raise ValueError(
                f"topic {topic_id!r} perf_chart {chart_id!r}: bad regex: {exc}") from exc
        for g in _PC_REQUIRED_GROUPS[mode]:
            if g == "label" and spec.get("from"):
                continue
            if g not in groups:
                raise ValueError(
                    f"topic {topic_id!r} perf_chart {chart_id!r}: {mode} regex "
                    f"must have a named group (?P<{g}>…)")
    return block


def _topic(d: dict) -> TopicTemplate:
    for key in _REQUIRED:
        if key not in d:
            raise ValueError(f"topic YAML missing required field {key!r}: {d.get('id', '?')}")
    cases = d.get("cases")
    controls = [_control(c) for c in d.get("controls", [])]
    standards = list(d.get("standards", []))
    if standards:
        dropdowns = [c.id for c in controls if c.kind == "dropdown"]
        if dropdowns:
            raise ValueError(
                f"topic {d.get('id', '?')!r} uses standards:{standards} but also "
                f"has dropdown control(s) {dropdowns}; a standards topic may not "
                f"have a competing tab row (see std-variant-axis spec)"
            )
        if len(set(standards)) != len(standards):
            raise ValueError(
                f"topic {d.get('id', '?')!r} has duplicate standards {standards}; "
                f"each standard must appear at most once (it becomes one tab)"
            )
    perf_chart = _validate_perf_chart(d.get("perf_chart") or {}, d.get("id", "?"))
    flag_variants = [_flag_variant(f) for f in d.get("flag_variants", [])]
    if flag_variants:
        dropdowns = [c.id for c in controls if c.kind == "dropdown"]
        if dropdowns:
            raise ValueError(
                f"topic {d.get('id', '?')!r} uses flag_variants but also has "
                f"dropdown control(s) {dropdowns}; a flag-variant axis owns the "
                f"tab row and may not compete with a dropdown"
            )
        if standards:
            raise ValueError(
                f"topic {d.get('id', '?')!r} sets both standards and "
                f"flag_variants; a topic tabs on ONE compiler axis, not both"
            )
        labels = [f["label"] for f in flag_variants]
        if len(set(labels)) != len(labels):
            raise ValueError(
                f"topic {d.get('id', '?')!r} has duplicate flag_variant labels "
                f"{labels}; each label becomes one tab and must be unique"
            )
    return TopicTemplate(
        id=d["id"],
        name=d["name"],
        template=d["template"],
        controls=controls,
        explanation=d["explanation"],
        group=d["group"],
        target_var=d.get("target_var", "x"),
        sanitize=d.get("sanitize", False),
        has_ptrdata=d.get("has_ptrdata", True),
        byte_decode=d.get("byte_decode", ""),
        byte_label=d.get("byte_label", ""),
        doc_url=d.get("doc_url", ""),
        cases=[_case(c) for c in cases] if cases else None,
        extra_compile_flags=list(d.get("extra_compile_flags", [])),
        standards=standards,
        flag_variants=flag_variants,
        perf_chart=perf_chart,
    )



def load_topics(topics_dir: Path) -> dict[str, TopicTemplate]:
    """Return ``{id: TopicTemplate}`` for all ``*.topic.yaml`` in *topics_dir*.

    Keyed by id and sorted by id for a stable, reproducible order. The order in
    which examples actually appear in a demonstration is set by the layout's
    ``demos:`` list — not here — so a topic file needs no ``order:`` field.
    """
    docs = [yaml.safe_load(p.read_text()) for p in topics_dir.glob("*.topic.yaml")]
    docs.sort(key=lambda d: d.get("id", ""))
    return {d["id"]: _topic(d) for d in docs}


def discover_topics(root: Path) -> dict[str, TopicTemplate]:
    """Return one ``{id: TopicTemplate}`` registry for every subject under *root*.

    Scans ``root/*/topics`` — each subject folder that owns a ``topics/`` dir
    contributes its topic files — and merges them into a single id-keyed
    registry. A subject that only *reuses* another's topics (no ``topics/`` dir
    of its own) is skipped; its page still resolves those ids from this merged
    set. This is what lets a brand-new subject be pure YAML: drop a folder with
    a ``topics/`` dir and a layout, and the engine finds it with no code change.

    Args:
        root: The package root holding the subject folders (i.e. ``cpp_labs/``).

    Returns:
        A ``{id: TopicTemplate}`` mapping across all subjects. If two subjects
        define the same id, the last one scanned (by sorted path) wins.
    """
    reg: dict[str, TopicTemplate] = {}
    for topics_dir in sorted(root.glob("*/topics")):
        reg.update(load_topics(topics_dir))
    return reg
