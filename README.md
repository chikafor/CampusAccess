# Campus Access

A Python command-line application for managing campus access-card requests. It uses only the Python standard library and stores records as JSON.

## Requirements

- Python 3.9 or newer
- No third-party packages

## Run the application

From the repository root:

```bash
python main.py
```

The default data file is `data/requests.json`, located under the project directory. On a first run, a missing file means there are no saved requests yet. The file and directory are created when a successful change is saved. Malformed or invalid saved data produces a clear error; the application will not silently replace it with an empty collection.

## Run tests

```bash
python -m unittest discover -s tests -v
```

## Request fields

Each request has exactly five fields:

- `id`: generated ID such as `A001`
- `fellow_id`: nonblank fellow identifier
- `card_type`: `visitor`, `student`, or `staff`
- `status`: `requested`, `approved`, `issued`, or `returned`
- `approved_by`: `null` until approval; the approver identifier afterward

Surrounding whitespace is trimmed from fellow and approver IDs. Blank values and wrong types are rejected.

## Workflow

`requested -> approved -> issued -> returned`

Approval requires a nonblank approver ID. Only requests in the correct current status can move to the next step. Rejected operations do not mutate the stored record.

Request IDs continue from the highest existing numeric suffix. For example, existing IDs `A001`, `A002`, and `A005` lead to next ID `A006`.

## Project files

- `main.py`: interactive CLI
- `request_manager.py`: validation, request IDs, and workflow transitions
- `storage.py`: JSON validation and atomic persistence
- `tests/`: standard-library unit tests
- `docs/design-decisions.md`: agreed design choices
- `docs/ai-learning-log.md`: template for recording actual learning cycles

Runtime data should not be committed to Git. The default `data/requests.json` is ignored by `.gitignore`.
