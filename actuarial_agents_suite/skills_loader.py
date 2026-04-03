"""Load and compose bundled Agent Skills from `skills/`."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Literal

from config import RESERVING_CORE_INSTRUCTIONS

PACKAGE_DIR = Path(__file__).resolve().parent
SKILLS_ROOT = PACKAGE_DIR / "skills"
SKILL_SEPARATOR = "\n\n---\n\n"

MissingSkillPolicy = Literal["strict", "skip"]


@dataclass(frozen=True)
class SkillLoadResult:
    skill_name: str
    content: str
    included_supporting_files: tuple[str, ...] = ()


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


def _load_supporting_skill_docs(skill_dir_name: str) -> tuple[str, tuple[str, ...]]:
    """
    Load optional supporting docs for a skill directory.

    Includes:
    - `AGENTS.md`
    - `rules/*.md`
    """
    skill_dir = SKILLS_ROOT / skill_dir_name
    included: list[str] = []
    blocks: list[str] = []

    agents_md = skill_dir / "AGENTS.md"
    if agents_md.is_file():
        included.append("AGENTS.md")
        blocks.append(f"## Supporting guide ({skill_dir_name}/AGENTS.md)\n\n{agents_md.read_text(encoding='utf-8').strip()}")

    rules_dir = skill_dir / "rules"
    if rules_dir.is_dir():
        for rule_file in sorted(rules_dir.glob("*.md")):
            rel = f"rules/{rule_file.name}"
            included.append(rel)
            blocks.append(f"## Rule ({skill_dir_name}/{rel})\n\n{rule_file.read_text(encoding='utf-8').strip()}")

    return SKILL_SEPARATOR.join(blocks), tuple(included)


def load_skill_bundle(skill_dir_name: str, *, include_supporting_docs: bool = True) -> SkillLoadResult:
    """Load one skill body and optional supporting docs into a single bundle."""
    base = load_skill_body(skill_dir_name).strip()
    supporting_content = ""
    included: tuple[str, ...] = ()
    if include_supporting_docs:
        supporting_content, included = _load_supporting_skill_docs(skill_dir_name)
    full = base if not supporting_content else (base + SKILL_SEPARATOR + supporting_content)
    return SkillLoadResult(
        skill_name=skill_dir_name,
        content=full,
        included_supporting_files=included,
    )


def concatenate_skills(
    skill_names: Iterable[str],
    *,
    separator: str = SKILL_SEPARATOR,
    include_supporting_docs: bool = True,
    missing_policy: MissingSkillPolicy = "strict",
) -> str:
    """Concatenate skills with shared missing-file behavior."""
    parts: list[str] = []
    for name in skill_names:
        try:
            bundle = load_skill_bundle(name, include_supporting_docs=include_supporting_docs)
            parts.append(bundle.content)
        except FileNotFoundError:
            if missing_policy == "skip":
                continue
            raise
    return separator.join(parts)


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
    base_skills = ["actuarial-senior-practice", "data-analyst", "visualization-expert", "technical-writer"]
    if extra_skill_dirs:
        for s in extra_skill_dirs:
            if s not in base_skills:
                base_skills.append(s)
    body = concatenate_skills(
        base_skills,
        include_supporting_docs=True,
        missing_policy="skip",
    )
    return SKILL_SEPARATOR.join([body, RESERVING_CORE_INSTRUCTIONS.strip()])


def compose_simple_system_prompt(*skill_dir_names: str) -> str:
    """Concatenate listed skills (bodies only) with separators."""
    return concatenate_skills(skill_dir_names, include_supporting_docs=False, missing_policy="strict")


AGENT_SKILL_STACKS: dict[str, list[str]] = {
    "reserving": [
        "actuarial-senior-practice",
        "data-analyst",
        "visualization-expert",
        "technical-writer",
        "actuarial-reserving-pc",
    ],
    "pricing": [
        "actuarial-senior-practice",
        "actuarial-life-health-pricing",
        "data-analyst",
        "decision-helper",
        "deep-research",
    ],
    "experience_study": [
        "actuarial-senior-practice",
        "actuarial-experience-study",
        "data-analyst",
        "visualization-expert",
        "actuarial-life-health-pricing",
    ],
    "model_validation": [
        "actuarial-senior-practice",
        "actuarial-model-validation",
        "python-expert",
        "code-reviewer",
    ],
}


def compose_agent_prompt(
    skill_names: list[str],
    extra_block: str = "",
    *,
    include_supporting_docs: bool = True,
    missing_policy: MissingSkillPolicy = "strict",
) -> str:
    """Build a system prompt from ordered skills plus optional freeform instructions."""
    body = concatenate_skills(
        skill_names,
        include_supporting_docs=include_supporting_docs,
        missing_policy=missing_policy,
    )
    if extra_block.strip():
        return body + SKILL_SEPARATOR + extra_block.strip()
    return body


def compose_prompt_for_role(
    role: str,
    *,
    extra_block: str = "",
    extra_skills: list[str] | None = None,
    missing_policy: MissingSkillPolicy = "strict",
) -> str:
    """Compose a deterministic prompt for one role defined in `AGENT_SKILL_STACKS`."""
    if role not in AGENT_SKILL_STACKS:
        raise KeyError(f"Unknown role: {role}")
    skills = list(AGENT_SKILL_STACKS[role])
    if extra_skills:
        for name in extra_skills:
            if name not in skills:
                skills.append(name)
    return compose_agent_prompt(
        skills,
        extra_block=extra_block,
        include_supporting_docs=True,
        missing_policy=missing_policy,
    )
