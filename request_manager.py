"""Business logic for Campus Access request records."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import storage

PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_STORAGE_PATH = PROJECT_ROOT / "data" / "requests.json"
_REQUEST_ID_PATTERN = re.compile(r"A[0-9]{3,}\Z")


class RequestManager:
    """Manage requests without exposing mutable internal records."""

    def __init__(self) -> None:
        self._requests: dict[str, dict[str, Any]] = {}
        self._next_id = 1

    def create_request(self, fellow_id: str, card_type: str) -> dict[str, Any]:
        """Create a request and return a defensive copy."""
        fellow_id = self._normalize_nonblank(fellow_id, "fellow_id")
        if not isinstance(card_type, str) or card_type not in storage.CARD_TYPES:
            raise ValueError("card_type must be one of: visitor, student, staff.")

        request_id = f"A{self._next_id:03d}"
        record = {
            "id": request_id,
            "fellow_id": fellow_id,
            "card_type": card_type,
            "status": "requested",
            "approved_by": None,
        }
        # Validate before mutating the manager.
        record = storage.validate_record(record)
        self._requests[request_id] = record
        self._next_id += 1
        return record.copy()

    def get_request(self, request_id: str) -> dict[str, Any]:
        """Return a copy of a request, never the internal dictionary."""
        record = self._find_request(request_id)
        return record.copy()

    def list_requests(self) -> list[dict[str, Any]]:
        """Return copies of all records in creation/loaded order."""
        return [record.copy() for record in self._requests.values()]

    def approve_request(self, request_id: str, approved_by: str) -> dict[str, Any]:
        record = self._find_request(request_id)
        approver = self._normalize_nonblank(approved_by, "approved_by")
        if record["status"] != "requested":
            raise ValueError("Only requested cards can be approved.")

        updated = record.copy()
        updated["status"] = "approved"
        updated["approved_by"] = approver
        self._requests[request_id] = storage.validate_record(updated)
        return self._requests[request_id].copy()

    def issue_card(self, request_id: str) -> dict[str, Any]:
        record = self._find_request(request_id)
        if record["status"] != "approved":
            raise ValueError("Only approved cards can be issued.")

        updated = record.copy()
        updated["status"] = "issued"
        self._requests[request_id] = storage.validate_record(updated)
        return self._requests[request_id].copy()

    def return_card(self, request_id: str) -> dict[str, Any]:
        record = self._find_request(request_id)
        if record["status"] != "issued":
            raise ValueError("Only issued cards can be returned.")

        updated = record.copy()
        updated["status"] = "returned"
        self._requests[request_id] = storage.validate_record(updated)
        return self._requests[request_id].copy()

    def save_requests(self, path: str | Path = DEFAULT_STORAGE_PATH) -> None:
        storage.save_requests(path, self._requests.values())

    def load_requests(self, path: str | Path = DEFAULT_STORAGE_PATH) -> None:
        """Replace memory only after the entire file has loaded successfully."""
        loaded = storage.load_requests(path)
        replacement = {record["id"]: record for record in loaded}
        self._requests = replacement
        self._next_id = max(
            (int(request_id[1:]) for request_id in replacement),
            default=0,
        ) + 1

    @staticmethod
    def _normalize_nonblank(value: Any, field_name: str) -> str:
        if not isinstance(value, str):
            raise ValueError(f"{field_name} must be a string.")
        normalized = value.strip()
        if not normalized:
            raise ValueError(f"{field_name} must not be blank.")
        return normalized

    def _find_request(self, request_id: str) -> dict[str, Any]:
        if not isinstance(request_id, str) or _REQUEST_ID_PATTERN.fullmatch(request_id) is None:
            raise ValueError("request_id must use the format A followed by at least three ASCII digits.")
        try:
            return self._requests[request_id]
        except KeyError as exc:
            raise ValueError(f"Request not found: {request_id}.") from exc
