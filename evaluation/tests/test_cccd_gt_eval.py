from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "evaluation" / "scripts"
for path in (ROOT, SCRIPTS):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import run_cccd_gt_eval as gt_eval
from llm_local.cccd_schema import response_format


class CccdGtEvalTests(unittest.TestCase):
    def test_input_messages_encodes_image_data_url_and_omits_assistant(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            image_path = Path(tmp) / "sample.jpg"
            image_path.write_bytes(b"image-bytes")
            record = {
                "messages": [
                    {"role": "system", "content": "system"},
                    {"role": "user", "content": "<image>\nReturn JSON."},
                    {"role": "assistant", "content": "{}"},
                ],
                "images": ["sample.jpg"],
            }

            messages = gt_eval.input_messages(record, image_path)

        self.assertEqual(messages[0], {"role": "system", "content": "system"})
        self.assertEqual(messages[1]["role"], "user")
        self.assertEqual(messages[1]["content"][0], {"type": "text", "text": "Return JSON."})
        self.assertEqual(messages[1]["content"][1]["type"], "image_url")
        self.assertTrue(messages[1]["content"][1]["image_url"]["url"].startswith("data:image/jpeg;base64,"))

    def test_response_format_is_strict_for_front_and_back(self) -> None:
        front = response_format("front")
        back = response_format("back")

        self.assertTrue(front["json_schema"]["strict"])
        self.assertFalse(front["json_schema"]["schema"]["additionalProperties"])
        self.assertIn("id_number", front["json_schema"]["schema"]["properties"]["fields"]["required"])
        self.assertTrue(back["json_schema"]["strict"])
        self.assertIn("mrz", back["json_schema"]["schema"]["properties"]["fields"]["required"])
        self.assertIn("document_number", back["json_schema"]["schema"]["properties"]["fields"]["properties"]["mrz"]["required"])

    def test_score_prediction_reports_exact_and_field_accuracy(self) -> None:
        expected = {
            "document_type": "cccd",
            "side": "front",
            "fields": {
                "id_number": "001",
                "full_name": "A",
                "date_of_birth": None,
                "gender": "Nam",
                "nationality": "Việt Nam",
                "place_of_origin": "HN",
                "date_of_expiry": "2030",
                "place_of_residence": "HN",
            },
        }
        predicted = json.loads(json.dumps(expected, ensure_ascii=False))
        predicted["fields"]["full_name"] = "B"

        score = gt_eval.score_prediction(expected, predicted, "front")

        self.assertFalse(score["exact_match"])
        self.assertEqual(score["matched_fields"], 7)
        self.assertEqual(score["total_fields"], 8)
        self.assertFalse(score["field_matches"]["fields.full_name"]["match"])

    def test_score_prediction_normalizes_string_case_and_spacing(self) -> None:
        expected = {
            "document_type": "cccd",
            "side": "front",
            "fields": {
                "id_number": "001",
                "full_name": "NGUYEN VAN A",
                "date_of_birth": None,
                "gender": "Nam",
                "nationality": "Viet Nam",
                "place_of_origin": "Ha Noi",
                "date_of_expiry": "2030",
                "place_of_residence": "Ha Noi",
            },
        }
        predicted = json.loads(json.dumps(expected, ensure_ascii=False))
        predicted["fields"]["full_name"] = "  nguyen   van   a  "
        predicted["fields"]["gender"] = "NAM"
        predicted["fields"]["nationality"] = "VIET   NAM"

        score = gt_eval.score_prediction(expected, predicted, "front")

        self.assertTrue(score["exact_match"])
        self.assertEqual(score["matched_fields"], 8)
        self.assertTrue(score["field_matches"]["fields.full_name"]["match"])
        self.assertTrue(score["field_matches"]["fields.gender"]["match"])
        self.assertTrue(score["field_matches"]["fields.nationality"]["match"])

    def test_evaluate_record_reports_http_payload_and_prediction(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            image_path = root / "sample.jpg"
            image_path.write_bytes(b"image-bytes")
            expected = {
                "document_type": "cccd",
                "side": "front",
                "fields": {
                    "id_number": "001",
                    "full_name": "A",
                    "date_of_birth": None,
                    "gender": None,
                    "nationality": None,
                    "place_of_origin": None,
                    "date_of_expiry": None,
                    "place_of_residence": None,
                },
            }
            record = {
                "_line_number": 1,
                "messages": [
                    {"role": "system", "content": "system"},
                    {"role": "user", "content": "<image>\nReturn JSON."},
                    {"role": "assistant", "content": json.dumps(expected)},
                ],
                "images": ["sample.jpg"],
            }

            def fake_post_chat_completion(**kwargs):
                self.assertEqual(kwargs["side"], "front")
                self.assertEqual(kwargs["model"], "local-vllm")
                self.assertEqual(kwargs["messages"][0]["role"], "system")
                return {"choices": [{"message": {"content": json.dumps(expected)}}]}

            with patch.object(gt_eval, "post_chat_completion", side_effect=fake_post_chat_completion):
                detail = gt_eval.evaluate_record(
                    record=record,
                    repo_root=root,
                    side="front",
                    base_url="http://example.test/v1",
                    api_key="key",
                    model="local-vllm",
                    timeout=1,
                    max_tokens=256,
                )

        self.assertTrue(detail["request_success"])
        self.assertTrue(detail["parse_success"])
        self.assertTrue(detail["schema_success"])
        self.assertTrue(detail["exact_match"])
        self.assertEqual(detail["matched_fields"], 8)

    def test_evaluate_record_reports_missing_image(self) -> None:
        record = {
            "_line_number": 1,
            "messages": [
                {"role": "user", "content": "<image>\nReturn JSON."},
                {"role": "assistant", "content": "{}"},
            ],
            "images": ["missing.jpg"],
        }

        detail = gt_eval.evaluate_record(
            record=record,
            repo_root=Path("/tmp"),
            side="front",
            base_url="http://example.test/v1",
            api_key=None,
            model="local-vllm",
            timeout=1,
            max_tokens=256,
        )

        self.assertFalse(detail["request_success"])
        self.assertFalse(detail["parse_success"])
        self.assertFalse(detail["schema_success"])
        self.assertIn("image not found", detail["error"])

    def test_schema_errors_reports_extra_and_missing_keys(self) -> None:
        payload = {
            "document_type": "cccd",
            "side": "front",
            "fields": {
                "id_number": "001",
                "full_name": "A",
                "date_of_birth": None,
                "gender": None,
                "nationality": None,
                "place_of_origin": None,
                "date_of_expiry": None,
                "extra": "bad",
            },
        }

        errors = gt_eval.schema_errors(payload, "front")

        self.assertIn("fields.place_of_residence is missing", errors)
        self.assertIn("fields.extra is not allowed", errors)

    def test_schema_errors_rejects_enum_casing_mismatch(self) -> None:
        payload = {
            "document_type": "CCCD",
            "side": "front",
            "fields": {
                "id_number": "001",
                "full_name": "A",
                "date_of_birth": None,
                "gender": None,
                "nationality": None,
                "place_of_origin": None,
                "date_of_expiry": None,
                "place_of_residence": None,
            },
        }

        errors = gt_eval.schema_errors(payload, "front")

        self.assertIn("document_type must equal 'cccd'", errors)

    def test_write_json_writes_array_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "details.json"
            payload = [{"predicted": {"document_type": "cccd"}, "expected": {"document_type": "cccd"}}]

            gt_eval.write_json(path, payload)

            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), payload)


if __name__ == "__main__":
    unittest.main()
