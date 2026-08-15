"""Skill-level defaults for declarative animations (md_to_yaml compiler).

Deck YAML may set ``animation_defaults`` in frontmatter; when omitted, these
values apply. Per-slide ``bullet_animation`` overrides merge on top.
"""
from __future__ import annotations

#: Default GSAP bundle URL when ``gsap_script_url`` is not set in deck metadata.
SKILL_GSAP_SCRIPT_URL_DEFAULT: str = (
    'https://cdn.jsdelivr.net/npm/gsap@3/dist/gsap.min.js'
)

#: Base parameters for ``bullet_animation`` / ``animation_defaults.bullet_stagger``.
SKILL_BULLET_STAGGER_DEFAULTS: dict[str, float | str] = {
    'duration': 0.45,
    'stagger': 0.12,
    'ease': 'power2.out',
    'threshold': 0.45,
    'x_offset': -24.0,
}

#: Base parameters for ``bullet_focus`` / ``animation_defaults.bullet_focus``.
#: ``key`` is the keyboard key that advances the focused bullet.
#: ``back_key`` is the keyboard key that reverses the focused bullet.
#: ``dim`` is the opacity applied to non-focused bullets.
SKILL_BULLET_FOCUS_DEFAULTS: dict[str, float | str] = {
    'key': 'j',
    'back_key': 'k',
    'dim': 0.25,
    'duration': 0.3,
    'ease': 'power2.out',
}
