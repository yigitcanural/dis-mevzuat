from __future__ import annotations

import math
from typing import Iterable

import httpx


class EmbeddingClient:
    def __init__(self, api_key: str | None, api_base: str, model: str, timeout: float):
        self.api_key = api_key
        self.api_base = api_base.rstrip("/")
        self.model = model
        self.timeout = timeout

    @property
    def enabled(self) -> bool:
        return bool(self.api_key)

    async def embed(self, texts: list[str], input_type: str | None = None) -> list[list[float]]:
        if not self.api_key:
            raise RuntimeError("Semantik arama için embedding API anahtarı yapılandırılmamış.")
        payload: dict = {"model": self.model, "input": texts, "encoding_format": "float"}
        if input_type:
            payload["input_type"] = input_type
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.api_base}/embeddings", headers=headers, json=payload
            )
            response.raise_for_status()
            body = response.json()
        ordered = sorted(body["data"], key=lambda item: item.get("index", 0))
        return [item["embedding"] for item in ordered]


def cosine_similarity(a: Iterable[float], b: Iterable[float]) -> float:
    a_values = list(a)
    b_values = list(b)
    if len(a_values) != len(b_values) or not a_values:
        return 0.0
    dot = sum(x * y for x, y in zip(a_values, b_values))
    norm_a = math.sqrt(sum(x * x for x in a_values))
    norm_b = math.sqrt(sum(y * y for y in b_values))
    if not norm_a or not norm_b:
        return 0.0
    return dot / (norm_a * norm_b)
