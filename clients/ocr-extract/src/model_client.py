import base64
import json
import re
from typing import Any

import httpx
from fastapi import HTTPException

from .config import env_int, litellm_api_key, litellm_base_url, required_env
from .documents import PageImage


class VisionModelClient:
    async def complete_json(
        self,
        *,
        prompt: str,
        pages: list[PageImage],
        response_format: dict[str, Any],
    ) -> dict[str, Any]:
        payload = {
            "model": required_env("LITELLM_MODEL"),
            "messages": [
                {
                    "role": "user",
                    "content": self._content_parts(prompt, pages),
                }
            ],
            "response_format": response_format,
        }
        timeout = env_int("REQUEST_TIMEOUT_SECONDS", 120)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                f"{litellm_base_url()}/chat/completions",
                headers={"Authorization": f"Bearer {litellm_api_key()}"},
                json=payload,
            )
        if response.status_code >= 400:
            raise HTTPException(status_code=502, detail=response.text)

        try:
            data = response.json()
        except ValueError as exc:
            raise HTTPException(status_code=502, detail=f"model returned invalid response JSON: {exc}") from exc

        return parse_json_content(message_content(data), data)

    def _content_parts(self, prompt: str, pages: list[PageImage]) -> list[dict[str, Any]]:
        parts: list[dict[str, Any]] = [{"type": "text", "text": prompt}]
        for page in pages:
            image_b64 = base64.b64encode(page.content).decode("ascii")
            parts.extend(
                [
                    {"type": "text", "text": f"Physical page {page.page_number}:"},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{page.mime_type};base64,{image_b64}",
                        },
                    },
                ]
            )
        return parts


def message_content(data: dict[str, Any]) -> str:
    message = ((data.get("choices") or [{}])[0].get("message") or {})
    refusal = message.get("refusal")
    if refusal:
        raise HTTPException(status_code=502, detail=f"model refused request: {refusal}")

    content = message.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for part in content:
            if isinstance(part, dict) and isinstance(part.get("text"), str):
                parts.append(part["text"])
        return "\n".join(parts)
    return ""


def parse_json_content(content: str, raw_response: dict[str, Any] | None = None) -> dict[str, Any]:
    text = content.strip()
    if not text and raw_response is not None:
        parsed = ((raw_response.get("choices") or [{}])[0].get("message") or {}).get("parsed")
        if isinstance(parsed, dict):
            return parsed
    if not text:
        raise HTTPException(status_code=502, detail="model returned empty content")
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    text = extract_json_object_text(text)
    try:
        parsed_json = json.loads(text)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"model returned invalid JSON: {exc}. content_prefix={text[:500]!r}",
        ) from exc
    if not isinstance(parsed_json, dict):
        raise HTTPException(status_code=502, detail="model JSON response must be an object")
    return parsed_json


def extract_json_object_text(text: str) -> str:
    starts = [index for index, char in enumerate(text) if char == "{"]
    if not starts:
        return text

    for start in starts:
        in_string = False
        escaped = False
        depth = 0
        for index in range(start, len(text)):
            char = text[index]
            if in_string:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    in_string = False
                continue

            if char == '"':
                in_string = True
            elif char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    return text[start:index + 1].strip()
    return text
