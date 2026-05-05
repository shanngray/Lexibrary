"""Tests for init/rules/codex.py — Codex environment rule generation."""

from __future__ import annotations

import json
import stat
import tomllib
from pathlib import Path

from lexibrary.init.rules.codex import generate_codex_rules
from lexibrary.init.rules.markers import MARKER_END, MARKER_START

# ---------------------------------------------------------------------------
# Create from scratch
# ---------------------------------------------------------------------------


class TestCreateFromScratch:
    """AGENTS.md created from scratch when file does not exist."""

    def test_creates_agents_md(self, tmp_path: Path) -> None:
        """generate_codex_rules() creates AGENTS.md at the project root."""
        generate_codex_rules(tmp_path)
        assert (tmp_path / "AGENTS.md").exists()

    def test_agents_md_has_markers(self, tmp_path: Path) -> None:
        """Created AGENTS.md contains both start and end markers."""
        generate_codex_rules(tmp_path)
        content = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
        assert MARKER_START in content
        assert MARKER_END in content

    def test_agents_md_has_core_rules(self, tmp_path: Path) -> None:
        """Created AGENTS.md contains core Lexibrary rules."""
        generate_codex_rules(tmp_path)
        content = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
        assert "TOPOLOGY.md" in content
        assert "lexi lookup" in content

    def test_agents_md_has_topology_reference(self, tmp_path: Path) -> None:
        """Created AGENTS.md references TOPOLOGY.md for session start."""
        generate_codex_rules(tmp_path)
        content = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
        assert "TOPOLOGY.md" in content

    def test_agents_md_has_search_content(self, tmp_path: Path) -> None:
        """Created AGENTS.md includes core search workflow guidance."""
        generate_codex_rules(tmp_path)
        content = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
        assert "lexi search" in content

    def test_returns_all_created_paths(self, tmp_path: Path) -> None:
        """Return value includes all generated Codex files."""
        result = generate_codex_rules(tmp_path)
        assert len(result) == 14

        filenames = [p.name for p in result]
        assert "AGENTS.md" in filenames
        assert "explore.toml" in filenames
        assert "plan.toml" in filenames
        assert "code.toml" in filenames
        assert "lexi-research.toml" in filenames
        assert "hooks.json" in filenames
        assert "lexi-pre-edit.sh" in filenames
        assert "lexi-post-edit.sh" in filenames

        skill_parents = {p.parent.name for p in result if p.name == "SKILL.md"}
        assert skill_parents == {
            "lexi-search",
            "lexi-lookup",
            "lexi-concept",
            "lexi-stack",
            "topology-builder",
        }


# ---------------------------------------------------------------------------
# Append to existing AGENTS.md
# ---------------------------------------------------------------------------


class TestAppendToExisting:
    """Existing AGENTS.md without markers gets section appended."""

    def test_preserves_existing_content(self, tmp_path: Path) -> None:
        """User content before the Lexibrary section is preserved."""
        agents_md = tmp_path / "AGENTS.md"
        user_content = "# My Agent Instructions\n\nDo important things.\n"
        agents_md.write_text(user_content, encoding="utf-8")

        generate_codex_rules(tmp_path)

        content = agents_md.read_text(encoding="utf-8")
        assert "# My Agent Instructions" in content
        assert "Do important things." in content

    def test_appends_markers(self, tmp_path: Path) -> None:
        """Markers are appended to existing content."""
        agents_md = tmp_path / "AGENTS.md"
        agents_md.write_text("# Existing content", encoding="utf-8")

        generate_codex_rules(tmp_path)

        content = agents_md.read_text(encoding="utf-8")
        assert MARKER_START in content
        assert MARKER_END in content

    def test_existing_content_before_markers(self, tmp_path: Path) -> None:
        """Existing content appears before the marker block."""
        agents_md = tmp_path / "AGENTS.md"
        agents_md.write_text("# Existing content", encoding="utf-8")

        generate_codex_rules(tmp_path)

        content = agents_md.read_text(encoding="utf-8")
        existing_pos = content.index("# Existing content")
        marker_pos = content.index(MARKER_START)
        assert existing_pos < marker_pos


# ---------------------------------------------------------------------------
# Update existing marked section
# ---------------------------------------------------------------------------


class TestUpdateExistingSection:
    """AGENTS.md with existing markers has section replaced."""

    def test_replaces_old_section(self, tmp_path: Path) -> None:
        """Old content between markers is replaced."""
        agents_md = tmp_path / "AGENTS.md"
        old_content = (
            f"# Custom Header\n\n"
            f"{MARKER_START}\n"
            f"outdated lexibrary rules\n"
            f"{MARKER_END}\n\n"
            f"# Custom Footer"
        )
        agents_md.write_text(old_content, encoding="utf-8")

        generate_codex_rules(tmp_path)

        content = agents_md.read_text(encoding="utf-8")
        assert "outdated lexibrary rules" not in content
        assert "TOPOLOGY.md" in content

    def test_preserves_surrounding_content(self, tmp_path: Path) -> None:
        """Content before and after the marker block is preserved."""
        agents_md = tmp_path / "AGENTS.md"
        old_content = (
            f"# Custom Header\n\n{MARKER_START}\nold stuff\n{MARKER_END}\n\n# Custom Footer"
        )
        agents_md.write_text(old_content, encoding="utf-8")

        generate_codex_rules(tmp_path)

        content = agents_md.read_text(encoding="utf-8")
        assert "# Custom Header" in content
        assert "# Custom Footer" in content

    def test_only_one_marker_pair(self, tmp_path: Path) -> None:
        """After update, there is exactly one start and one end marker."""
        agents_md = tmp_path / "AGENTS.md"
        old_content = f"{MARKER_START}\nold\n{MARKER_END}"
        agents_md.write_text(old_content, encoding="utf-8")

        generate_codex_rules(tmp_path)

        content = agents_md.read_text(encoding="utf-8")
        assert content.count(MARKER_START) == 1
        assert content.count(MARKER_END) == 1

    def test_updated_section_removes_old_embedded_skill_body(self, tmp_path: Path) -> None:
        """Updating an old Codex block removes stale inline skill frontmatter."""
        agents_md = tmp_path / "AGENTS.md"
        old_content = (
            f"{MARKER_START}\n"
            "---\nname: lexi-search\ndescription: old embedded skill\n---\n"
            "old embedded skill body\n"
            f"{MARKER_END}"
        )
        agents_md.write_text(old_content, encoding="utf-8")

        generate_codex_rules(tmp_path)

        content = agents_md.read_text(encoding="utf-8")
        assert "old embedded skill body" not in content
        assert "name: lexi-search" not in content


# ---------------------------------------------------------------------------
# Skill files
# ---------------------------------------------------------------------------


class TestSkillFiles:
    """Codex repo-scoped skills are created in .agents/skills/."""

    def test_creates_repo_scoped_skills(self, tmp_path: Path) -> None:
        """Core Lexibrary skills are written under .agents/skills."""
        generate_codex_rules(tmp_path)

        for skill_name in ("lexi-search", "lexi-lookup", "lexi-concept", "lexi-stack"):
            skill = tmp_path / ".agents" / "skills" / skill_name / "SKILL.md"
            assert skill.exists()

    def test_search_skill_has_valid_frontmatter(self, tmp_path: Path) -> None:
        """Skill templates keep AgentSkills-compatible frontmatter."""
        import yaml  # noqa: PLC0415

        generate_codex_rules(tmp_path)
        skill = tmp_path / ".agents" / "skills" / "lexi-search" / "SKILL.md"
        content = skill.read_text(encoding="utf-8")

        assert content.startswith("---")
        end = content.index("---", 3)
        frontmatter = yaml.safe_load(content[3:end].strip())
        assert frontmatter["name"] == "lexi-search"
        assert frontmatter["description"]
        assert "lexi search" in content

    def test_skill_files_overwritten_on_update(self, tmp_path: Path) -> None:
        """Regeneration refreshes stale skill files."""
        skill = tmp_path / ".agents" / "skills" / "lexi-search" / "SKILL.md"
        skill.parent.mkdir(parents=True, exist_ok=True)
        skill.write_text("old search content", encoding="utf-8")

        generate_codex_rules(tmp_path)

        content = skill.read_text(encoding="utf-8")
        assert "old search content" not in content
        assert "lexi search" in content

    def test_creates_topology_builder_skill_assets(self, tmp_path: Path) -> None:
        """topology-builder gets its asset template."""
        generate_codex_rules(tmp_path)
        template = (
            tmp_path / ".agents" / "skills" / "topology-builder" / "assets" / "topology_template.md"
        )
        assert template.exists()


# ---------------------------------------------------------------------------
# Custom agents
# ---------------------------------------------------------------------------


class TestCustomAgents:
    """Codex custom agents are created as TOML files."""

    def test_creates_custom_agents(self, tmp_path: Path) -> None:
        """Custom agents are written under .codex/agents."""
        generate_codex_rules(tmp_path)

        for agent_name in ("explore", "plan", "code", "lexi-research"):
            assert (tmp_path / ".codex" / "agents" / f"{agent_name}.toml").exists()

    def test_agent_toml_has_required_fields(self, tmp_path: Path) -> None:
        """Custom agent TOML contains Codex-required fields."""
        generate_codex_rules(tmp_path)
        agent = tmp_path / ".codex" / "agents" / "explore.toml"
        data = tomllib.loads(agent.read_text(encoding="utf-8"))

        assert data["name"] == "Explore"
        assert data["description"]
        assert "developer_instructions" in data
        assert "lexi search" in data["developer_instructions"]

    def test_agent_files_overwritten_on_update(self, tmp_path: Path) -> None:
        """Regeneration refreshes stale custom agent files."""
        agent = tmp_path / ".codex" / "agents" / "plan.toml"
        agent.parent.mkdir(parents=True, exist_ok=True)
        agent.write_text('name = "Old"\n', encoding="utf-8")

        generate_codex_rules(tmp_path)

        data = tomllib.loads(agent.read_text(encoding="utf-8"))
        assert data["name"] == "Plan"
        assert "Old" not in data["developer_instructions"]


# ---------------------------------------------------------------------------
# Hooks
# ---------------------------------------------------------------------------


class TestHooks:
    """Codex hook config and scripts are generated."""

    def test_creates_hooks_json(self, tmp_path: Path) -> None:
        """hooks.json uses Codex's project-local hook shape."""
        generate_codex_rules(tmp_path)
        hooks_file = tmp_path / ".codex" / "hooks.json"

        data = json.loads(hooks_file.read_text(encoding="utf-8"))
        assert "hooks" in data
        assert "PreToolUse" in data["hooks"]
        assert "PostToolUse" in data["hooks"]

        pre_hook = data["hooks"]["PreToolUse"][0]["hooks"][0]
        assert pre_hook["type"] == "command"
        assert pre_hook["command"].endswith(".codex/hooks/lexi-pre-edit.sh")

    def test_hooks_json_additively_merges_existing_hooks(self, tmp_path: Path) -> None:
        """Existing hook entries are preserved during generation."""
        hooks_file = tmp_path / ".codex" / "hooks.json"
        hooks_file.parent.mkdir(parents=True, exist_ok=True)
        hooks_file.write_text(
            json.dumps(
                {
                    "hooks": {
                        "Stop": [
                            {
                                "matcher": "*",
                                "hooks": [{"type": "command", "command": "echo stop"}],
                            }
                        ]
                    },
                    "custom": True,
                }
            ),
            encoding="utf-8",
        )

        generate_codex_rules(tmp_path)

        data = json.loads(hooks_file.read_text(encoding="utf-8"))
        assert data["custom"] is True
        assert data["hooks"]["Stop"][0]["hooks"][0]["command"] == "echo stop"
        assert "PreToolUse" in data["hooks"]

    def test_hook_scripts_are_executable(self, tmp_path: Path) -> None:
        """Generated hook scripts are executable."""
        generate_codex_rules(tmp_path)

        for script_name in ("lexi-pre-edit.sh", "lexi-post-edit.sh"):
            script = tmp_path / ".codex" / "hooks" / script_name
            assert script.exists()
            mode = script.stat().st_mode
            assert mode & stat.S_IXUSR

    def test_hook_scripts_are_overwritten_on_update(self, tmp_path: Path) -> None:
        """Regeneration refreshes stale hook scripts."""
        script = tmp_path / ".codex" / "hooks" / "lexi-pre-edit.sh"
        script.parent.mkdir(parents=True, exist_ok=True)
        script.write_text("old hook", encoding="utf-8")

        generate_codex_rules(tmp_path)

        content = script.read_text(encoding="utf-8")
        assert "old hook" not in content
        assert "lexi lookup" in content
