import json
import tempfile
import unittest
from pathlib import Path

from request_manager import RequestManager
from storage import load_requests, save_requests


VALID_RECORD = {
    "id": "A001",
    "fellow_id": "F001",
    "card_type": "visitor",
    "status": "requested",
    "approved_by": None,
}


class StorageTests(unittest.TestCase):
    def test_missing_file_returns_empty_list(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(load_requests(Path(directory) / "missing.json"), [])

    def test_round_trip(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "data" / "requests.json"
            save_requests(path, [VALID_RECORD])
            self.assertEqual(load_requests(path), [VALID_RECORD])

    def test_malformed_json_raises_clear_value_error(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "requests.json"
            path.write_text("{oops", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "invalid JSON"):
                load_requests(path)

    def test_rejects_non_array_document(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "requests.json"
            path.write_text(json.dumps({"request": VALID_RECORD}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "array"):
                load_requests(path)

    def test_rejects_missing_or_extra_keys(self):
        for record in (
            {key: value for key, value in VALID_RECORD.items() if key != "approved_by"},
            {**VALID_RECORD, "unexpected": True},
        ):
            with self.subTest(record=record), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "requests.json"
                path.write_text(json.dumps([record]), encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "Invalid request record"):
                    load_requests(path)

    def test_rejects_duplicate_ids(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "requests.json"
            path.write_text(json.dumps([VALID_RECORD, VALID_RECORD]), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Duplicate request id"):
                load_requests(path)

    def test_rejects_invalid_status_and_card_type(self):
        for changes in ({"status": "issued"}, {"card_type": "Visitor"}):
            record = {**VALID_RECORD, **changes}
            with self.subTest(changes=changes), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "requests.json"
                path.write_text(json.dumps([record]), encoding="utf-8")
                with self.assertRaises(ValueError):
                    load_requests(path)

    def test_failed_load_preserves_manager_state(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "requests.json"
            self.manager = RequestManager()
            self.manager.create_request("F001", "visitor")
            original = self.manager.list_requests()
            path.write_text("{bad json", encoding="utf-8")
            with self.assertRaises(ValueError):
                self.manager.load_requests(path)
            self.assertEqual(self.manager.list_requests(), original)

    def test_failed_save_does_not_replace_destination(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "requests.json"
            path.write_text("preserve this", encoding="utf-8")
            with self.assertRaises(ValueError):
                save_requests(path, [{"not": "a request"}])
            self.assertEqual(path.read_text(encoding="utf-8"), "preserve this")


if __name__ == "__main__":
    unittest.main()
