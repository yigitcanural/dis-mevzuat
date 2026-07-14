from __future__ import annotations

import json
import tomllib
from pathlib import Path

import pytest
from fastmcp import Client


ROOT = Path(__file__).resolve().parents[1]
READ_ONLY_TOOLS = {
    "search_sources",
    "list_sources",
    "get_source",
    "get_chunk",
    "system_status",
}


def test_claude_uses_canonical_agent_instructions() -> None:
    assert (ROOT / "CLAUDE.md").read_text(encoding="utf-8").strip() == "@AGENTS.md"
    assert (ROOT / "AGENTS.md").is_file()
    assert (ROOT / "docs" / "PROJECT_CONTEXT.md").is_file()


def test_claude_project_mcp_is_portable_and_read_only() -> None:
    config = json.loads((ROOT / ".mcp.json").read_text(encoding="utf-8"))
    server = config["mcpServers"]["dis-mevzuat"]

    assert server["type"] == "stdio"
    assert "${CLAUDE_PROJECT_DIR:-.}" in server["command"]
    assert server["args"] == ["serve"]
    assert server["env"]["DM_ENABLE_ADMIN_TOOLS"] == "false"
    assert server["env"]["DM_TRANSPORT"] == "stdio"


def test_codex_project_mcp_exposes_only_read_tools() -> None:
    with (ROOT / ".codex" / "config.toml").open("rb") as handle:
        config = tomllib.load(handle)
    server = config["mcp_servers"]["dis_mevzuat"]

    assert server["command"] == ".venv/bin/dis-mevzuat"
    assert set(server["enabled_tools"]) == READ_ONLY_TOOLS
    assert server["env"]["DM_ENABLE_ADMIN_TOOLS"] == "false"
    assert server["env"]["DM_TRANSPORT"] == "stdio"


def test_client_skill_wrappers_point_to_the_canonical_skill() -> None:
    canonical = ROOT / "skills" / "review-dental-content" / "SKILL.md"
    assert canonical.is_file()

    for client_dir in (".claude", ".agents"):
        wrapper = ROOT / client_dir / "skills" / "review-dental-content" / "SKILL.md"
        text = wrapper.read_text(encoding="utf-8")
        assert text.startswith("---\nname: review-dental-content\n")
        assert "../../../skills/review-dental-content/SKILL.md" in text


@pytest.mark.asyncio
async def test_default_mcp_surface_is_read_only(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DM_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("DM_ENABLE_ADMIN_TOOLS", "false")
    monkeypatch.setenv("DM_TRANSPORT", "stdio")

    from dis_mevzuat.server import mcp

    async with Client(mcp) as client:
        tools = await client.list_tools()

    assert {tool.name for tool in tools} == READ_ONLY_TOOLS
