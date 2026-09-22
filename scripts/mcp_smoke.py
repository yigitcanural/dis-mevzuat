#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio

from fastmcp import Client


EXPECTED = {
    "search_regulations",
    "list_sources",
    "get_source",
    "get_chunk",
    "get_source_status",
    "system_status",
}
FORBIDDEN = {
    "preview_source",
    "preview_text_source",
    "approve_source",
    "check_source_update",
    "archive_source",
    "delete_source",
    "reindex",
}


async def smoke(url: str, query: str) -> None:
    async with Client(url) as client:
        tools = await client.list_tools()
        names = {tool.name for tool in tools}
        assert names == EXPECTED, f"Unexpected tool inventory: {sorted(names)}"
        assert not (names & FORBIDDEN)
        for tool in tools:
            assert tool.description
            assert tool.annotations and tool.annotations.readOnlyHint is True
            assert tool.annotations.destructiveHint is False
            assert tool.annotations.openWorldHint is False

        status = (await client.call_tool("system_status", {})).data
        search = (
            await client.call_tool(
                "search_regulations", {"query": query, "top_k": 3, "current_only": True}
            )
        ).data
        assert search["result_count"] > 0, "Smoke query returned no evidence"
        hit = search["results"][0]
        chunk = (
            await client.call_tool("get_chunk", {"chunk_id": hit["meta"]["chunk_id"]})
        ).data
        assert chunk["evidence"]["official_url"].startswith("https://")
        print(
            {
                "handshake": "ok",
                "tools": sorted(names),
                "status": status,
                "query": query,
                "top_result": {
                    "title": chunk["meta"]["title"],
                    "article_or_chunk": chunk["data"]["article_or_chunk"],
                    "official_url": chunk["evidence"]["official_url"],
                    "source_status": chunk["evidence"]["source_status"],
                    "publication_date": chunk["meta"]["publication_date"],
                },
            }
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("url", help="Remote MCP URL, for example https://host.example/mcp")
    parser.add_argument(
        "--query", default="öncesi sonrası görsel paylaşım açık rıza"
    )
    args = parser.parse_args()
    asyncio.run(smoke(args.url, args.query))


if __name__ == "__main__":
    main()
