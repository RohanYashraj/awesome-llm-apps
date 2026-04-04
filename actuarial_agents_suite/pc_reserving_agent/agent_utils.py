"""Helpers for this standalone agent package."""

from __future__ import annotations

import os


def load_skill_markdown(skill_subdir: str) -> str:
    """Load SKILL.md body, stripping YAML front matter for cleaner LLM context."""
    path = os.path.join(os.path.dirname(__file__), "skills", skill_subdir, "SKILL.md")
    if not os.path.isfile(path):
        return ""
    with open(path, encoding="utf-8") as f:
        text = f.read()
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            text = text[end + 4 :].lstrip("\n")
    return text.strip()
