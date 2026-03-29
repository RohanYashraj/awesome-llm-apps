"""Load Agent Skills from the bundled `skills/` directory (self-contained)."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

from config import RESERVING_CORE_INSTRUCTIONS

PACKAGE_DIR = Path(__file__).resolve().parent
SKILLS_ROOT = PACKAGE_DIR / "skills"


def skill_exists(skill_dir_name: str) -> bool:
    """Return True if `skills/<name>/SKILL.md` exists."""
    return (SKILLS_ROOT / skill_dir_name / "SKILL.md").is_file()


def _strip_yaml_frontmatter(markdown: str) -> str:
    """Remove leading YAML frontmatter (--- ... ---) from SKILL.md body."""
    text = markdown.strip()
    if not text.startswith("---"):
        return text
    parts = text.split("---", 2)
    if len(parts) >= 3:
        return parts[2].strip()
    return text


def load_skill_markdown(skill_dir_name: str) -> str:
    """Return full SKILL.md text for a skill directory name (e.g. `data-analyst`)."""
    path = SKILLS_ROOT / skill_dir_name / "SKILL.md"
    if not path.is_file():
        raise FileNotFoundError(f"Skill not found: {path}")
    return path.read_text(encoding="utf-8")


def load_skill_body(skill_dir_name: str) -> str:
    """Return SKILL.md with YAML frontmatter removed (for LLM system prompts)."""
    return _strip_yaml_frontmatter(load_skill_markdown(skill_dir_name))


def concatenate_skills(skill_names: Iterable[str], separator: str = "\n\n---\n\n") -> str:
    return separator.join(load_skill_body(name) for name in skill_names)


def compose_reserving_system_prompt(
    extra_skill_dirs: list[str] | None = None,
) -> str:
    """
    Build the reserving assistant system prompt from shared skills + core reserving instructions.

    Parameters
    ----------
    extra_skill_dirs
        Optional additional skill directory names under `skills/` (e.g. `actuarial-reserving-pc`).
    """
    parts: list[str] = []
    base_skills = ["data-analyst", "visualization-expert", "technical-writer"]
    if extra_skill_dirs:
        for s in extra_skill_dirs:
            if s not in base_skills:
                base_skills.append(s)
    for name in base_skills:
        try:
            parts.append(load_skill_body(name))
        except FileNotFoundError:
            continue
    parts.append(RESERVING_CORE_INSTRUCTIONS)
    return "\n\n---\n\n".join(parts)


def compose_simple_system_prompt(*skill_dir_names: str) -> str:
    """Concatenate listed skills (bodies only) with separators."""
    return concatenate_skills(skill_dir_names)


def compose_agent_prompt(skill_names: list[str], extra_block: str = "") -> str:
    """Build a system prompt from an ordered list of skills plus optional freeform instructions."""
    body = concatenate_skills(skill_names)
    if extra_block.strip():
        return body + "\n\n---\n\n" + extra_block.strip()
    return body
