#!/usr/bin/env python3
"""Evaluate a LiteLLM vision model against the CCCD ground-truth dataset."""

from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from llm_local.cccd_compare import (
    get_path as compare_get_path,
    normalize_cccd_value,
    schema_errors as compare_schema_errors,
    score_cccd_payload,
)
from llm_local.cccd_schema import field_paths, response_format

DEFAULT_BASE_URL = "http://localhost:18040/v1"
DEFAULT_DATASET_DIR = ROOT / "datasets" / "cccd_qwen3_vl"
DEFAULT_RESULTS_DIR = ROOT / "evaluation" / "results" / "cccd_gt_eval"


def json_dumps(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def safe_model_name(model: str) -> str:
    chars = []
    for char in model.lower():
        if char.isalnum():
            chars.append(char)
        elif chars and chars[-1] != "-":
            chars.append("-")
    return "".join(chars).strip("-") or "model"


def data_url_for_image(path: Path) -> str:
    mime_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def normalize_for_compare(value: Any) -> Any:
    return normalize_cccd_value(value)


def get_path(payload: dict[str, Any], path: str) -> Any:
    return compare_get_path(payload, path)


def score_prediction(expected: dict[str, Any], predicted: dict[str, Any], side: str) -> dict[str, Any]:
    return score_cccd_payload(expected, predicted, side)


def schema_errors(payload: dict[str, Any], side: str) -> list[str]:
    return compare_schema_errors(payload, side)


def load_dataset(path: Path, *, limit: int | None = None) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if limit is not None and len(records) >= limit:
                break
            record = json.loads(line)
            record["_line_number"] = line_number
            records.append(record)
    return records


def expected_payload(record: dict[str, Any]) -> dict[str, Any]:
    for message in record["messages"]:
        if message.get("role") == "assistant":
            content = message.get("content", "")
            parsed = json.loads(content)
            if not isinstance(parsed, dict):
                raise ValueError("assistant ground truth must be a JSON object")
            return parsed
    raise ValueError("record has no assistant ground-truth message")


def input_messages(record: dict[str, Any], image_path: Path) -> list[dict[str, Any]]:
    system_messages = [
        {"role": message["role"], "content": message["content"]}
        for message in record["messages"]
        if message.get("role") == "system"
    ]
    user = next((message for message in record["messages"] if message.get("role") == "user"), None)
    if user is None:
        raise ValueError("record has no user message")
    prompt = str(user.get("content", "")).replace("<image>\n", "").replace("<image>", "").strip()
    return [
        *system_messages,
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": data_url_for_image(image_path)}},
            ],
        },
    ]


def extract_message_content(response: dict[str, Any]) -> str:
    message = ((response.get("choices") or [{}])[0].get("message") or {})
    content = message.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(part["text"] for part in content if isinstance(part, dict) and isinstance(part.get("text"), str))
    parsed = message.get("parsed")
    if isinstance(parsed, dict):
        return json_dumps(parsed)
    return ""


def parse_json_object(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.removeprefix("```json").removeprefix("```").strip()
        stripped = stripped.removesuffix("```").strip()
    parsed = json.loads(stripped)
    if not isinstance(parsed, dict):
        raise ValueError("model response JSON must be an object")
    return parsed


def post_chat_completion(
    *,
    base_url: str,
    api_key: str | None,
    model: str,
    messages: list[dict[str, Any]],
    side: str,
    timeout: int,
    max_tokens: int,
) -> dict[str, Any]:
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0,
        "max_tokens": max_tokens,
        "response_format": response_format(side),
    }
    body = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    request = Request(f"{base_url.rstrip('/')}/chat/completions", data=body, headers=headers, method="POST")
    with urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def evaluate_record(
    *,
    record: dict[str, Any],
    repo_root: Path,
    side: str,
    base_url: str,
    api_key: str | None,
    model: str,
    timeout: int,
    max_tokens: int,
) -> dict[str, Any]:
    image_rel = record["images"][0]
    image_path = repo_root / image_rel
    expected = expected_payload(record)
    started = time.time()
    detail: dict[str, Any] = {
        "line_number": record.get("_line_number"),
        "side": side,
        "image": image_rel,
        "expected": expected,
        "predicted": None,
        "raw_response": None,
        "error": None,
        "schema_errors": [],
    }
    try:
        if not image_path.is_file():
            raise FileNotFoundError(f"image not found: {image_rel}")
        response = post_chat_completion(
            base_url=base_url,
            api_key=api_key,
            model=model,
            messages=input_messages(record, image_path),
            side=side,
            timeout=timeout,
            max_tokens=max_tokens,
        )
        detail["raw_response"] = response
        predicted = parse_json_object(extract_message_content(response))
        detail["predicted"] = predicted
        detail["schema_errors"] = schema_errors(predicted, side)
        detail.update(score_prediction(expected, predicted, side))
        detail["parse_success"] = True
        detail["schema_success"] = not detail["schema_errors"]
        detail["request_success"] = True
    except HTTPError as exc:
        detail["error"] = f"HTTP {exc.code}: {exc.read().decode('utf-8', errors='replace')[:1000]}"
        detail.update(empty_score(side))
    except (URLError, TimeoutError, OSError, ValueError, json.JSONDecodeError) as exc:
        detail["error"] = str(exc)
        detail.update(empty_score(side))
    finally:
        detail["latency_s"] = round(time.time() - started, 4)
    return detail


def empty_score(side: str) -> dict[str, Any]:
    total = len(field_paths(side))
    return {
        "parse_success": False,
        "schema_success": False,
        "request_success": False,
        "exact_match": False,
        "field_matches": {},
        "matched_fields": 0,
        "total_fields": total,
        "field_accuracy": 0,
    }


def summarize(details: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(details)
    request_success = sum(1 for item in details if item.get("request_success"))
    parse_success = sum(1 for item in details if item.get("parse_success"))
    schema_success = sum(1 for item in details if item.get("schema_success"))
    exact_matches = sum(1 for item in details if item.get("exact_match"))
    matched_fields = sum(int(item.get("matched_fields") or 0) for item in details)
    total_fields = sum(int(item.get("total_fields") or 0) for item in details)
    latencies = [float(item["latency_s"]) for item in details if item.get("request_success")]
    return {
        "samples": total,
        "request_success": request_success,
        "request_success_rate": request_success / total if total else 0,
        "parse_success": parse_success,
        "parse_success_rate": parse_success / total if total else 0,
        "schema_success": schema_success,
        "schema_success_rate": schema_success / total if total else 0,
        "exact_matches": exact_matches,
        "exact_match_rate": exact_matches / total if total else 0,
        "matched_fields": matched_fields,
        "total_fields": total_fields,
        "field_accuracy": matched_fields / total_fields if total_fields else 0,
        "avg_latency_s": round(sum(latencies) / len(latencies), 4) if latencies else 0,
        "min_latency_s": round(min(latencies), 4) if latencies else 0,
        "max_latency_s": round(max(latencies), 4) if latencies else 0,
    }


def first_error(details: list[dict[str, Any]]) -> str | None:
    for item in details:
        error = item.get("error")
        if error:
            image = item.get("image", "unknown image")
            return f"{image}: {error}"
    return None


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True, help="LiteLLM model alias to evaluate.")
    parser.add_argument(
        "--base-url",
        default=os.environ.get("LITELLM_BASE_URL", DEFAULT_BASE_URL),
        help="OpenAI-compatible LiteLLM base URL, including /v1.",
    )
    parser.add_argument(
        "--api-key",
        default=os.environ.get("LITELLM_API_KEY") or os.environ.get("LITELLM_MASTER_KEY", "sk-local-litellm"),
        help="Optional LiteLLM bearer token.",
    )
    parser.add_argument("--dataset-dir", type=Path, default=DEFAULT_DATASET_DIR, help="CCCD Qwen3-VL dataset directory.")
    parser.add_argument("--output-dir", type=Path, default=None, help="Directory for summary/detail artifacts.")
    parser.add_argument("--split", choices=["front", "back", "all"], default="all", help="Dataset split to evaluate.")
    parser.add_argument("--limit", type=int, default=None, help="Limit samples per selected split.")
    parser.add_argument("--timeout", type=int, default=120, help="Per-request timeout in seconds.")
    parser.add_argument("--max-tokens", type=int, default=1024, help="Max tokens for the model response.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    splits = ["front", "back"] if args.split == "all" else [args.split]
    now = datetime.now()
    run_id = f"{safe_model_name(args.model)}_{now.strftime('%H%M%S')}"
    output_dir = args.output_dir or DEFAULT_RESULTS_DIR / now.strftime("%Y%m%d")
    output_dir = output_dir.resolve()
    detail_prefix = "" if args.output_dir else f"{run_id}_"

    split_summaries: dict[str, Any] = {}
    all_details: list[dict[str, Any]] = []
    any_request_success = False
    for side in splits:
        dataset_path = args.dataset_dir.resolve() / side / "train.jsonl"
        records = load_dataset(dataset_path, limit=args.limit)
        details = [
            evaluate_record(
                record=record,
                repo_root=ROOT,
                side=side,
                base_url=args.base_url,
                api_key=args.api_key,
                model=args.model,
                timeout=args.timeout,
                max_tokens=args.max_tokens,
            )
            for record in records
        ]
        write_json(output_dir / side / f"{detail_prefix}details.json", details)
        split_summaries[side] = summarize(details)
        all_details.extend(details)
        any_request_success = any_request_success or any(item.get("request_success") for item in details)
        print(f"{side}: {split_summaries[side]}")
        error = first_error(details)
        if error:
            print(f"{side} first_error: {error}")

    summary = {
        "model": args.model,
        "base_url": args.base_url,
        "dataset_dir": str(args.dataset_dir),
        "output_dir": str(output_dir),
        "split": args.split,
        "limit": args.limit,
        "run_id": run_id,
        "timestamp": now.isoformat(),
        "overall": summarize(all_details),
        "splits": split_summaries,
    }
    summary_path = output_dir / f"{detail_prefix}summary.json"
    if args.split == "all":
        write_json(output_dir / f"{detail_prefix}details.json", all_details)
    write_json(summary_path, summary)
    print(f"summary: {summary_path}")
    if all_details and not any_request_success:
        print("ERROR: no requests succeeded; inspect details.json for full error payloads")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
