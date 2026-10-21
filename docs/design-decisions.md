# Design Decisions — Campus Access

> Status: Decisions 1–4 are confirmed by the project owner; remaining decisions are proposals pending review.

## 1. Request record

Each request is a dictionary with exactly these keys:

```python
{
    "id": "A001",
    "fellow_id": "F001",
    "card_type": "visitor",
    "status": "requested",
    "approved_by": None,
}
```

Allowed card types are `visitor`, `student`, and `staff`. Allowed statuses are `requested`, `approved`, `issued`, and `returned`.

## 2. Return values for create_request and get_request

`create_request(fellow_id, card_type)` will return a copy of the newly created record.

**Confirmed decision:** `get_request(request_id)` will also return a copy of the stored record, not the internal dictionary. This prevents callers from changing internal state directly and bypassing validation or workflow rules. Callers must use the manager's public operations to make changes.

## 3. Invalid-input behavior

Public operations will raise `ValueError` for invalid values, unknown request IDs, and unsupported workflow transitions. The CLI will catch expected user-input errors, display a helpful message, and continue running. Wrong Python types will be rejected rather than silently converted.

## 4. ID generation

**Confirmed decision:** Request IDs use the form `A001`, `A002`, `A003`, and so on. After loading valid records, the manager derives the next number from the highest existing numeric suffix rather than filling gaps. For example, if the existing IDs are `A001`, `A002`, and `A005`, the next ID is `A006`. This avoids reusing an ID simply because a lower number is missing. ID parsing will use ASCII digits only.

## 5. Storage ownership and module contract

The request manager owns in-memory records and business validation. The storage module handles JSON encoding/decoding and validates the shape and values of records being loaded. The agreed public interfaces are:

- `create_request(fellow_id, card_type)`
- `get_request(request_id)`
- `list_requests()`
- `approve_request(request_id, approved_by)`
- `issue_card(request_id)`
- `return_card(request_id)`
- `save_requests(path)`
- `load_requests(path)`

The exact module ownership and constructor signatures will be confirmed before implementation. The CLI must call these public functions rather than editing stored dictionaries directly.

## 6. Invalid JSON or invalid saved data

**Confirmed decision:** Loading will parse and validate the complete file into temporary data first. Only after all records pass validation will the manager replace its current in-memory data. Malformed JSON, missing or unexpected keys, invalid types or values, invalid IDs/statuses, and duplicate IDs will raise a clear error. A failed load must preserve existing in-memory records exactly as they were.

Saving will serialize the current records and report filesystem errors to the caller. Tests will verify that a failed save does not truncate or replace a valid destination file.

## 7. Data that must not change on rejected operations

For any rejected create, approval, issue, return, or load operation, existing records must remain unchanged. In particular, a failed transition must preserve all five fields of the affected record. Validation must happen before mutation.

## 8. Workflow invariants

Only these transitions are legal:

- `requested -> approved` when `approved_by` is a nonblank string.
- `approved -> issued` when `approved_by` is present and nonblank.
- `issued -> returned`.

There are no other transitions. `returned` is final.

## 9. Default storage location

**Confirmed decision:** The default JSON persistence file is `data/requests.json`, relative to the project directory. The application should create the `data` directory when needed and handle a missing file safely. Filesystem and JSON errors must be reported clearly. Saving should be implemented so that a failed write does not truncate or replace an existing valid file. Runtime data containing real personal information should not be committed to Git.

## 10. Open questions to verify

- Confirm whether extra keys in a JSON record should be rejected. Proposal: reject them to keep the schema exact.
- Confirm whether surrounding whitespace in a nonblank fellow ID or approver ID should be preserved or stripped. Proposal: reject blank-after-strip values and store the trimmed value.
- Confirm the exact behavior for first-run startup when `data/requests.json` does not exist.
