import pytest
from fastmcp import Client

from dis_mevzuat.admin_server import mcp as admin_mcp
from dis_mevzuat.server import mcp as public_mcp


PUBLIC_TOOLS = {
    "search_regulations",
    "list_sources",
    "get_source",
    "get_chunk",
    "get_source_status",
    "system_status",
}
ADMIN_TOOLS = {
    "preview_source",
    "preview_text_source",
    "approve_source",
    "check_source_update",
    "archive_source",
}


@pytest.mark.asyncio
async def test_public_tool_discovery_and_annotations():
    async with Client(public_mcp) as client:
        tools = await client.list_tools()
    assert {tool.name for tool in tools} == PUBLIC_TOOLS
    assert not ({tool.name for tool in tools} & ADMIN_TOOLS)
    for tool in tools:
        assert tool.description
        assert tool.annotations.readOnlyHint is True
        assert tool.annotations.destructiveHint is False
        assert tool.annotations.openWorldHint is False


@pytest.mark.asyncio
async def test_admin_is_a_separate_server():
    async with Client(admin_mcp) as client:
        tools = await client.list_tools()
    assert {tool.name for tool in tools} == ADMIN_TOOLS
    assert not ({tool.name for tool in tools} & PUBLIC_TOOLS)


@pytest.mark.asyncio
async def test_public_search_returns_structured_evidence():
    async with Client(public_mcp) as client:
        result = await client.call_tool(
            "search_regulations", {"query": "hasta öncesi sonrası fotoğraf", "top_k": 1}
        )
    assert result.data["result_count"] == 1
    hit = result.data["results"][0]
    assert {"data", "meta", "evidence", "retrieval"} <= hit.keys()
    assert hit["meta"]["current_or_archived"] == "current"
    assert hit["evidence"]["official_url"].startswith("https://")
