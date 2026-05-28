import asyncio

import pytest
from fastapi import HTTPException

from src.documents import PageImage
from src.model_client import VisionModelClient
from src.structured import strict_response_format


class FakeResponse:
    status_code = 200
    text = "{}"

    def json(self):
        return {"choices": [{"message": {"content": '{"documents":[]}'}}]}


class FakeAsyncClient:
    def __init__(self, *, timeout):
        self.timeout = timeout

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        return None

    async def post(self, url, headers, json):
        FakeAsyncClient.last_url = url
        FakeAsyncClient.last_headers = headers
        FakeAsyncClient.last_payload = json
        return FakeResponse()


def test_model_client_requires_litellm_model(monkeypatch):
    monkeypatch.delenv("LITELLM_MODEL", raising=False)

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(
            VisionModelClient().complete_json(
                prompt="Return JSON.",
                pages=[],
                response_format=strict_response_format(
                    "sample",
                    {"type": "object", "properties": {}, "required": [], "additionalProperties": False},
                ),
            )
        )

    assert exc_info.value.status_code == 500


def test_model_client_sends_strict_response_format(monkeypatch):
    import src.model_client as model_client

    monkeypatch.setenv("LITELLM_MODEL", "local-vllm")
    monkeypatch.setattr(model_client.httpx, "AsyncClient", FakeAsyncClient)

    response_format = strict_response_format(
        "sample",
        {"type": "object", "properties": {}, "required": [], "additionalProperties": False},
    )
    result = asyncio.run(
        VisionModelClient().complete_json(
            prompt="Return JSON.",
            pages=[PageImage(page_number=1, content=b"image", mime_type="image/png")],
            response_format=response_format,
        )
    )

    assert result == {"documents": []}
    assert FakeAsyncClient.last_payload["model"] == "local-vllm"
    assert FakeAsyncClient.last_payload["response_format"] == response_format
    assert FakeAsyncClient.last_payload["messages"][0]["content"][2]["type"] == "image_url"
