import tempfile
import unittest
from pathlib import Path

from request_manager import RequestManager


class RequestManagerTests(unittest.TestCase):
    def setUp(self):
        self.manager = RequestManager()

    def test_create_request_trims_fellow_id_and_returns_copy(self):
        result = self.manager.create_request(" F001 ", "visitor")
        self.assertEqual(result["fellow_id"], "F001")
        result["status"] = "issued"
        self.assertEqual(self.manager.get_request("A001")["status"], "requested")

    def test_rejects_blank_or_wrong_type_fellow_id_without_consuming_id(self):
        for invalid in ("   ", None, 123):
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    self.manager.create_request(invalid, "visitor")
        self.assertEqual(self.manager.create_request("F001", "visitor")["id"], "A001")

    def test_rejects_invalid_card_type_without_consuming_id(self):
        with self.assertRaises(ValueError):
            self.manager.create_request("F001", "Visitor")
        self.assertEqual(self.manager.create_request("F001", "visitor")["id"], "A001")

    def test_get_and_list_return_copies(self):
        self.manager.create_request("F001", "student")
        record = self.manager.get_request("A001")
        record["fellow_id"] = "CHANGED"
        listed = self.manager.list_requests()
        listed[0]["card_type"] = "staff"
        self.assertEqual(self.manager.get_request("A001")["fellow_id"], "F001")
        self.assertEqual(self.manager.get_request("A001")["card_type"], "student")

    def test_workflow_success_path(self):
        self.manager.create_request("F001", "staff")
        approved = self.manager.approve_request("A001", " admin ")
        self.assertEqual(approved["status"], "approved")
        self.assertEqual(approved["approved_by"], "admin")
        self.assertEqual(self.manager.issue_card("A001")["status"], "issued")
        self.assertEqual(self.manager.return_card("A001")["status"], "returned")

    def test_rejected_transitions_do_not_mutate_records(self):
        self.manager.create_request("F001", "visitor")
        original = self.manager.get_request("A001")
        operations = [
            lambda: self.manager.issue_card("A001"),
            lambda: self.manager.return_card("A001"),
            lambda: self.manager.approve_request("A001", "  "),
        ]
        for operation in operations:
            with self.assertRaises(ValueError):
                operation()
            self.assertEqual(self.manager.get_request("A001"), original)

    def test_invalid_transition_from_each_nonmatching_state(self):
        self.manager.create_request("F001", "visitor")
        self.manager.approve_request("A001", "admin")
        with self.assertRaises(ValueError):
            self.manager.approve_request("A001", "admin")
        self.manager.issue_card("A001")
        with self.assertRaises(ValueError):
            self.manager.issue_card("A001")
        self.manager.return_card("A001")
        with self.assertRaises(ValueError):
            self.manager.return_card("A001")

    def test_unknown_and_malformed_ids_rejected(self):
        for request_id in ("A1", "A００１", "A999", None):
            with self.subTest(request_id=request_id):
                with self.assertRaises(ValueError):
                    self.manager.get_request(request_id)

    def test_persistence_and_id_sequence_after_restart(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "data" / "requests.json"
            self.manager.create_request("F001", "visitor")
            self.manager.create_request("F002", "student")
            self.manager.save_requests(path)

            restored = RequestManager()
            restored.load_requests(path)
            self.assertEqual(len(restored.list_requests()), 2)
            self.assertEqual(restored.create_request("F003", "staff")["id"], "A003")

    def test_next_id_uses_highest_suffix_not_first_gap(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "requests.json"
            path.write_text(
                '[{"id":"A001","fellow_id":"F1","card_type":"visitor","status":"requested","approved_by":null},'
                '{"id":"A005","fellow_id":"F5","card_type":"staff","status":"requested","approved_by":null}]',
                encoding="utf-8",
            )
            self.manager.load_requests(path)
            self.assertEqual(self.manager.create_request("F6", "student")["id"], "A006")

    def test_missing_file_loads_empty_collection(self):
        with tempfile.TemporaryDirectory() as directory:
            self.manager.create_request("F001", "visitor")
            self.manager.load_requests(Path(directory) / "missing.json")
            self.assertEqual(self.manager.list_requests(), [])
            self.assertEqual(self.manager.create_request("F002", "staff")["id"], "A001")


if __name__ == "__main__":
    unittest.main()
