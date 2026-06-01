#!/usr/bin/env python3
"""Build Qwen3-VL training data for Vietnamese CCCD OCR.

This converter emits ms-swift-compatible multimodal JSONL with one image per
sample, strict schema prompts, and separate front/back splits.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from llm_local.cccd_schema import side_prompt

FRONT_FIELDS = {
    "id_number": 1,
    "full_name": 2,
    "date_of_birth": 3,
    "gender": 4,
    "nationality": 5,
    "place_of_origin": 6,
    "date_of_expiry": 7,
    "place_of_residence": 8,
}

BACK_FIELDS = {
    "special_mark": 9,
    "back_date": 10,
}

MRZ_FIELDS = {
    "country": 12,
    "document_number": 13,
    "document_number_checksum": 14,
    "document_number_checksum_validate": 15,
    "personal_number": 16,
    "personal_number_checksum": 17,
    "personal_number_checksum_validate": 18,
    "dob": 19,
    "dob_checksum": 20,
    "dob_checksum_validate": 21,
    "gender": 22,
    "due_date": 23,
    "due_date_checksum": 24,
    "due_date_checksum_validate": 25,
    "nationality": 26,
    "checksum": 27,
    "sur_name": 28,
    "given_name": 29,
}


def normalize_text(value: str) -> str:
    return unicodedata.normalize("NFKC", value).casefold()


def clean_cell(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def cell_value(row: list[str], index: int) -> str | None:
    if index >= len(row):
        return None
    return clean_cell(row[index])


def row_has_front_data(row: list[str]) -> bool:
    return any(cell_value(row, index) for index in range(1, 9))


def row_has_back_data(row: list[str]) -> bool:
    return any(cell_value(row, index) for index in [9, 10] + list(range(12, 30)))


def classify_side(row: list[str]) -> str | None:
    front = row_has_front_data(row)
    back = row_has_back_data(row)
    if front and back:
        raise ValueError("mixed front/back record is not supported")
    if front:
        return "front"
    if back:
        return "back"
    return None


def resolve_image_name(row: list[str]) -> str | None:
    for index in (0, 11):
        candidate = cell_value(row, index)
        if candidate:
            return candidate
    return None


def build_image_lookup(images_dir: Path) -> dict[str, Path]:
    lookup: dict[str, Path] = {}
    for path in sorted(images_dir.iterdir()):
        if not path.is_file():
            continue
        key = normalize_text(path.name)
        if key in lookup and lookup[key].name != path.name:
            raise ValueError(f"ambiguous image name normalization: {lookup[key].name!r} vs {path.name!r}")
        lookup[key] = path
    return lookup


def resolve_image_path(
    *,
    row: list[str],
    images_dir: Path,
    image_lookup: dict[str, Path],
) -> tuple[Path | None, str | None, str]:
    resolved_name = resolve_image_name(row)
    if not resolved_name:
        return None, None, "blank_name"

    exact_path = images_dir / resolved_name
    if exact_path.exists():
        return exact_path, resolved_name, "exact_match"

    normalized_path = image_lookup.get(normalize_text(resolved_name))
    if normalized_path is not None:
        return normalized_path, resolved_name, "normalized_match"

    return None, resolved_name, "missing_file"


def value_or_null(value: str | None) -> Any:
    return value if value is not None else None


def build_front_fields(row: list[str]) -> dict[str, str | None]:
    return {field_name: value_or_null(cell_value(row, index)) for field_name, index in FRONT_FIELDS.items()}


def build_back_fields(row: list[str]) -> dict[str, Any]:
    mrz = {field_name: value_or_null(cell_value(row, index)) for field_name, index in MRZ_FIELDS.items()}
    return {
        "special_mark": value_or_null(cell_value(row, BACK_FIELDS["special_mark"])),
        "back_date": value_or_null(cell_value(row, BACK_FIELDS["back_date"])),
        "mrz": mrz,
    }


def build_target_payload(row: list[str], side: str) -> dict[str, Any]:
    if side == "front":
        return {
            "document_type": "cccd",
            "side": "front",
            "fields": build_front_fields(row),
        }
    if side == "back":
        return {
            "document_type": "cccd",
            "side": "back",
            "fields": build_back_fields(row),
        }
    raise ValueError(f"unknown side: {side}")


def build_record(
    *,
    repo_root: Path,
    image_path: Path,
    assistant_payload: dict[str, Any],
    side: str,
) -> dict[str, Any]:
    system_prompt, user_prompt = side_prompt(side)
    return {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
            {
                "role": "assistant",
                "content": json.dumps(assistant_payload, ensure_ascii=False, separators=(",", ":")),
            },
        ],
        "images": [str(image_path.relative_to(repo_root).as_posix())],
    }


def load_rows(csv_path: Path) -> list[list[str]]:
    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        next(reader)
        return list(reader)


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False))
            handle.write("\n")


def write_json(path: Path, payload: Any) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--csv",
        type=Path,
        default=Path(__file__).resolve().parent / "Kết quả OCR căn cước công dân(GT).csv",
        help="Source CSV file.",
    )
    parser.add_argument(
        "--images-dir",
        type=Path,
        default=Path(__file__).resolve().parent / "Data test CCCD",
        help="Directory containing the source CCCD images.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parent / "cccd_qwen3_vl",
        help="Output directory for the split datasets.",
    )
    return parser.parse_args()


def build_split_outputs(csv_path: Path, images_dir: Path, output_dir: Path) -> dict[str, Any]:
    repo_root = csv_path.resolve().parents[1]
    rows = load_rows(csv_path)
    image_lookup = build_image_lookup(images_dir)
    all_image_names = {path.name for path in images_dir.iterdir() if path.is_file()}

    side_rows: dict[str, list[tuple[int, list[str]]]] = {"front": [], "back": []}
    skipped_rows: list[dict[str, Any]] = []
    reason_counts: Counter[str] = Counter()

    for csv_row, row in enumerate(rows, start=2):
        try:
            side = classify_side(row)
        except ValueError as exc:
            skipped_rows.append(
                {
                    "csv_row": csv_row,
                    "reason": "mixed_side",
                    "image_name": resolve_image_name(row),
                    "error": str(exc),
                }
            )
            reason_counts["mixed_side"] += 1
            continue

        image_path, image_name, resolution = resolve_image_path(
            row=row,
            images_dir=images_dir,
            image_lookup=image_lookup,
        )
        if image_path is None:
            skipped_rows.append(
                {
                    "csv_row": csv_row,
                    "reason": resolution,
                    "image_name": image_name,
                    "side": side,
                }
            )
            reason_counts[resolution] += 1
            continue

        if side is None:
            skipped_rows.append(
                {
                    "csv_row": csv_row,
                    "reason": "no_side_data",
                    "image_name": image_name,
                }
            )
            reason_counts["no_side_data"] += 1
            continue

        side_rows[side].append((csv_row, row))

    split_reports: dict[str, Any] = {}
    used_image_names: set[str] = set()

    for side in ("front", "back"):
        split_dir = output_dir / side
        split_dir.mkdir(parents=True, exist_ok=True)
        records: list[dict[str, Any]] = []
        side_discarded: list[dict[str, Any]] = []

        for csv_row, row in side_rows[side]:
            image_path, image_name, resolution = resolve_image_path(
                row=row,
                images_dir=images_dir,
                image_lookup=image_lookup,
            )
            if image_path is None:
                side_discarded.append(
                    {
                        "csv_row": csv_row,
                        "reason": resolution,
                        "image_name": image_name,
                        "side": side,
                    }
                )
                continue

            payload = build_target_payload(row, side)
            records.append(
                build_record(
                    repo_root=repo_root,
                    image_path=image_path,
                    assistant_payload=payload,
                    side=side,
                )
            )
            used_image_names.add(image_path.name)

        train_path = split_dir / "train.jsonl"
        pretty_path = split_dir / "train_pretty.json"
        qc_path = split_dir / "qc.json"

        write_jsonl(train_path, records)
        write_json(pretty_path, records)

        split_reports[side] = {
            "train_jsonl": str(train_path.relative_to(repo_root).as_posix()),
            "train_pretty_json": str(pretty_path.relative_to(repo_root).as_posix()),
            "counts": {
                "source_rows": len(side_rows[side]),
                "train_records": len(records),
                "discarded_rows": len(side_rows[side]) - len(records),
            },
            "discarded_rows": side_discarded,
        }

        write_json(qc_path, split_reports[side])

    unused_images = sorted(all_image_names - used_image_names)
    global_qc = {
        "source_csv": str(csv_path.relative_to(repo_root).as_posix()),
        "images_dir": str(images_dir.relative_to(repo_root).as_posix()),
        "output_dir": str(output_dir.relative_to(repo_root).as_posix()),
        "counts": {
            "csv_data_rows": len(rows),
            "front_source_rows": len(side_rows["front"]),
            "back_source_rows": len(side_rows["back"]),
            "front_train_records": split_reports["front"]["counts"]["train_records"],
            "back_train_records": split_reports["back"]["counts"]["train_records"],
            "discarded_rows": len(skipped_rows)
            + split_reports["front"]["counts"]["discarded_rows"]
            + split_reports["back"]["counts"]["discarded_rows"],
            "unused_images": len(unused_images),
        },
        "discarded_reason_counts": dict(sorted(reason_counts.items())),
        "discarded_rows": skipped_rows,
        "unused_images": unused_images,
        "split_reports": {
            side: {
                "train_jsonl": report["train_jsonl"],
                "train_pretty_json": report["train_pretty_json"],
                "counts": report["counts"],
            }
            for side, report in split_reports.items()
        },
        "notes": [
            "This dataset uses ms-swift standard messages format with one image per row.",
            "Relative image paths are resolved by setting ROOT_IMAGE_DIR to the repo root when training with ms-swift.",
            "Front and back are split into separate dataset folders to make single-side training easier.",
        ],
    }

    qc_path = output_dir / "qc.json"
    write_json(qc_path, global_qc)
    return global_qc


def main() -> int:
    args = parse_args()
    csv_path = args.csv.resolve()
    images_dir = args.images_dir.resolve()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    qc = build_split_outputs(csv_path, images_dir, output_dir)
    print(
        json.dumps(
            {
                "front_train_records": qc["counts"]["front_train_records"],
                "back_train_records": qc["counts"]["back_train_records"],
                "discarded_rows": qc["counts"]["discarded_rows"],
                "unused_images": qc["counts"]["unused_images"],
                "front_dataset": qc["split_reports"]["front"]["train_jsonl"],
                "back_dataset": qc["split_reports"]["back"]["train_jsonl"],
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
