"""Codex (OpenAI) environment rule generation.

Generates:
- ``AGENTS.md`` -- marker-delimited Lexibrary section containing core agent rules
- ``.agents/skills/*`` -- repo-scoped Codex skills
- ``.codex/agents/*.toml`` -- Codex custom subagents
- ``.codex/hooks.json`` and ``.codex/hooks/*.sh`` -- Codex lifecycle hooks

Codex reads project guidance from ``AGENTS.md`` and discovers repo skills from
``.agents/skills``.  Custom agents and hooks live under the project-scoped
``.codex`` config layer.  The marker-based ``AGENTS.md`` update preserves
user-authored content outside the Lexibrary section.
"""

from __future__ import annotations

import json
import shlex
import stat
from pathlib import Path

from lexibrary.init.rules.base import get_core_rules
from lexibrary.init.rules.markers import (
    append_lexibrary_section,
    has_lexibrary_section,
    replace_lexibrary_section,
)
from lexibrary.templates import read_template

_LEXI_SKILLS: tuple[str, ...] = (
    "lexi-search",
    "lexi-lookup",
    "lexi-concept",
    "lexi-stack",
)

_CODEX_AGENTS: tuple[str, ...] = (
    "explore",
    "plan",
    "code",
    "lexi-research",
)


def _generate_agents_md(project_root: Path) -> Path:
    """Create or update the marker-managed ``AGENTS.md`` file."""
    agents_md = project_root / "AGENTS.md"
    core_rules = get_core_rules()

    if agents_md.exists():
        existing = agents_md.read_text(encoding="utf-8")
        if has_lexibrary_section(existing):
            updated = replace_lexibrary_section(existing, core_rules)
        else:
            updated = append_lexibrary_section(existing, core_rules)
    else:
        updated = append_lexibrary_section("", core_rules)

    agents_md.write_text(updated, encoding="utf-8")
    return agents_md


def _deploy_lexi_skills(project_root: Path) -> list[Path]:
    """Deploy shared Lexibrary skill templates into Codex's repo skill location."""
    created: list[Path] = []
    skills_dir = project_root / ".agents" / "skills"
    skills_dir.mkdir(parents=True, exist_ok=True)

    for skill_name in _LEXI_SKILLS:
        content = read_template(f"rules/skills/{skill_name}/SKILL.md").strip()
        skill_dir = skills_dir / skill_name
        skill_dir.mkdir(parents=True, exist_ok=True)
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text(content + "\n", encoding="utf-8")
        created.append(skill_file)

    topology_dir = skills_dir / "topology-builder"
    topology_assets_dir = topology_dir / "assets"
    topology_assets_dir.mkdir(parents=True, exist_ok=True)

    topology_skill = topology_dir / "SKILL.md"
    topology_skill.write_text(
        read_template("rules/skills/topology-builder/SKILL.md").strip() + "\n",
        encoding="utf-8",
    )
    created.append(topology_skill)

    topology_template = topology_assets_dir / "topology_template.md"
    topology_template.write_text(
        read_template("rules/skills/topology-builder/assets/topology_template.md").strip() + "\n",
        encoding="utf-8",
    )
    created.append(topology_template)

    return created


def _generate_custom_agents(project_root: Path) -> list[Path]:
    """Deploy Codex custom-agent TOML templates."""
    agents_dir = project_root / ".codex" / "agents"
    agents_dir.mkdir(parents=True, exist_ok=True)

    created: list[Path] = []
    for agent_name in _CODEX_AGENTS:
        agent_file = agents_dir / f"{agent_name}.toml"
        agent_file.write_text(
            read_template(f"codex/agents/{agent_name}.toml").strip() + "\n",
            encoding="utf-8",
        )
        created.append(agent_file)

    return created


def _build_hooks_config(project_root: Path) -> dict[str, list[dict[str, object]]]:
    """Build Codex hook config with project-specific hook script paths."""
    pre_edit = shlex.quote(str(project_root / ".codex" / "hooks" / "lexi-pre-edit.sh"))
    post_edit = shlex.quote(str(project_root / ".codex" / "hooks" / "lexi-post-edit.sh"))
    return {
        "PreToolUse": [
            {
                "matcher": "Edit|Write",
                "hooks": [
                    {
                        "type": "command",
                        "command": pre_edit,
                        "timeout": 10000,
                    },
                ],
            },
        ],
        "PostToolUse": [
            {
                "matcher": "Edit|Write",
                "hooks": [
                    {
                        "type": "command",
                        "command": post_edit,
                        "timeout": 15000,
                    },
                ],
            },
        ],
    }


def _generate_hooks_json(project_root: Path) -> Path:
    """Create or additively merge ``.codex/hooks.json``."""
    codex_dir = project_root / ".codex"
    codex_dir.mkdir(parents=True, exist_ok=True)
    hooks_file = codex_dir / "hooks.json"

    if hooks_file.exists():
        hooks_json: dict[str, object] = json.loads(hooks_file.read_text(encoding="utf-8"))
    else:
        hooks_json = {}

    existing_hooks = hooks_json.get("hooks", {})
    if not isinstance(existing_hooks, dict):
        existing_hooks = {}

    for event_type, our_entries in _build_hooks_config(project_root).items():
        existing_entries = existing_hooks.get(event_type, [])
        if not isinstance(existing_entries, list):
            existing_entries = []

        existing_commands: set[str] = set()
        for entry in existing_entries:
            if not isinstance(entry, dict):
                continue
            hooks_list = entry.get("hooks", [])
            if not isinstance(hooks_list, list):
                continue
            for hook in hooks_list:
                if isinstance(hook, dict) and isinstance(hook.get("command"), str):
                    existing_commands.add(hook["command"])

        for our_entry in our_entries:
            our_hooks = our_entry.get("hooks", [])
            if not isinstance(our_hooks, list):
                continue
            if any(
                isinstance(hook, dict) and hook.get("command") not in existing_commands
                for hook in our_hooks
            ):
                existing_entries.append(our_entry)

        existing_hooks[event_type] = existing_entries

    hooks_json["hooks"] = existing_hooks
    hooks_file.write_text(json.dumps(hooks_json, indent=2) + "\n", encoding="utf-8")
    return hooks_file


def _generate_hook_scripts(project_root: Path) -> list[Path]:
    """Deploy executable Codex hook scripts."""
    hooks_dir = project_root / ".codex" / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)

    created: list[Path] = []
    for script_name in ("lexi-pre-edit.sh", "lexi-post-edit.sh"):
        script = hooks_dir / script_name
        script.write_text(
            read_template(f"codex/hooks/{script_name}").strip() + "\n",
            encoding="utf-8",
        )
        script.chmod(script.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        created.append(script)

    return created


def generate_codex_rules(project_root: Path) -> list[Path]:
    """Generate Codex agent rule files at *project_root*.

    Creates or updates:

    1. ``AGENTS.md`` — Lexibrary section appended (new file / no markers)
       or replaced (existing markers).  Includes core rules only.
    2. ``.agents/skills/`` — repo-scoped Lexibrary skill files.
    3. ``.codex/agents/`` — custom Codex subagent TOML files.
    4. ``.codex/hooks.json`` and ``.codex/hooks/`` — lifecycle hook config
       and scripts.

    Args:
        project_root: Absolute path to the project root directory.

    Returns:
        List of absolute paths to all created or updated files.
    """
    created: list[Path] = []

    created.append(_generate_agents_md(project_root))
    created.extend(_deploy_lexi_skills(project_root))
    created.extend(_generate_custom_agents(project_root))
    created.append(_generate_hooks_json(project_root))
    created.extend(_generate_hook_scripts(project_root))

    return created
