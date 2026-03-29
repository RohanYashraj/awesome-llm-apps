# Bundled Agent Skills

This directory contains **all** [Agent Skills](https://agentskills.io/specification) used by the Actuarial Agents Suite—**actuarial** skills plus supporting skills (data analysis, research, writing, etc.)—so the suite does **not** depend on the parent repo’s [`awesome_agent_skills/`](../../awesome_agent_skills/) tree.

- Each subdirectory is one skill (`SKILL.md` required; some include `rules/` or `AGENTS.md`).
- [`skills_loader.py`](../skills_loader.py) loads from **`skills/<name>/SKILL.md`** relative to the suite root.

To add or update a skill, edit the corresponding folder here and restart the Streamlit app.
