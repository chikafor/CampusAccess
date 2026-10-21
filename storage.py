"""JSON persistence for Campus Access requests.

The file format is a JSON array of request dictionaries. Loading validates the
whole file before returning any records; saving uses a temporary file and
atomic replacement to protect an existing valid file from partial writes.
"""
from __future__ import annotations

import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any, Iterable

REQUEST_KEYS = {"id", "fellow_id", "card_type", "status", "approved_by"}
CARD_TYPES = {"visitor", "student", "staff"}
STATUSES = {"requested", "approved", "issued", "returned"}
REQUEST_ID_PATTERN = re.compile(r"A[0-9]{3,}\Z")


def _trimmed_nonblank(value: Any, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string.")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must not be blank.")
    return normalized


def validate_record(record: Any) -> dict[str, Any]:
    """Validate and return a normalized copy of one request record."""
    if not isinstance(record, dict):
        raise ValueError("Each request record must be a JSON object.")

    keys = set(record)
    if keys != REQUEST_KEYS:
        missing = sorted(REQUEST_KEYS - keys)
        extra = sorted(keys - REQUEST_KEYS)
        details = []
        if missing:
            details.append("missing keys: " + ", ".join(missing))
        if extra:
            details.append("unexpected keys: " + ", ".join(map(str, extra)))
        raise ValueError("Invalid request record (" + "; ".join(details) + ").")

    request_id = record["id"]
    if not isinstance(request_id, str) or REQUEST_ID_PATTERN.fullmatch(request_id) is None:
        raise ValueError("Request id must use the format A followed by at least three ASCII digits.")

    fellow_id = _trimmed_nonblank(record["fellow_id"], "fellow_id")

    card_type = record["card_type"]
    if not isinstance(card_type, str) or card_type not in CARD_TYPES:
        raise ValueError("card_type must be one of: visitor, student, staff.")

    status = record["status"]
    if not isinstance(status, str) or status not in STATUSES:
        raise ValueError("status must be one of: requested, approved, issued, returned.")

    approved_by = record["approved_by"]
    if status == "requested":
        if approved_by is not None:
            raise ValueError("A requested record must have approved_by set to null.")
    else:
        approved_by = _trimmed_nonblank(approved_by, "approved_by")

    return {
        "id": request_id,
        "fellow_id": fellow_id,
        "card_type": card_type,
        "status": status,
        "approved_by": approved_by,
    }


def validate_records(records: Any) -> list[dict[str, Any]]:
    """Validate a complete collection and reject duplicate request IDs."""
    if not isinstance(records, list):
        raise ValueError("The JSON document must contain an array of request records.")

    validated: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for index, record in enumerate(records):
        try:
            clean_record = validate_record(record)
        except ValueError as exc:
            raise ValueError(f"Invalid request at index {index}: {exc}") from exc
        request_id = clean_record["id"]
        if request_id in seen_ids:
            raise ValueError(f"Duplicate request id: {request_id}.")
        seen_ids.add(request_id)
        validated.append(clean_record)
    return validated


def load_requests(path: str | os.PathLike[str]) -> list[dict[str, Any]]:
    """Load and validate all requests; a missing file means a fresh install."""
    file_path = Path(path)
    try:
        with file_path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Cannot load requests from {file_path}: invalid JSON at line "
            f"{exc.lineno}, column {exc.colno}."
        ) from exc
    except UnicodeDecodeError as exc:
        raise ValueError(f"Cannot load requests from {file_path}: file is not valid UTF-8.") from exc
    except OSError as exc:
        raise OSError(f"Cannot read requests from {file_path}: {exc}") from exc

    return validate_records(data)


def save_requests(
    path: str | os.PathLike[str], records: Iterable[dict[str, Any]]
) -> None:
    """Atomically save validated requests as a JSON array."""
    file_path = Path(path)
    validated = validate_records(list(records))
    file_path.parent.mkdir(parents=True, exist_ok=True)

    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            dir=file_path.parent,
            prefix=f".{file_path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary_name = handle.name
            json.dump(validated, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, file_path)
        temporary_name = None
    except OSError as exc:
        raise OSError(f"Cannot save requests to {file_path}: {exc}") from exc
    finally:
        if temporary_name is not None:
            try:
                os.unlink(temporary_name)
            except FileNotFoundError:
                pass
            except OSError:
                pass
