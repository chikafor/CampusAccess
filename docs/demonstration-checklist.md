# Demonstration Checklist

Run from the repository root with `python main.py`. Use test/demo identifiers only.

## Happy path

- [ ] Start with no `data/requests.json`; confirm the app starts with zero requests.
- [ ] Create a visitor request for `F001`; confirm it receives ID `A001` and status `requested`.
- [ ] Approve `A001` using approver `ADMIN1`; confirm status `approved` and approver is recorded.
- [ ] Issue `A001`; confirm status `issued`.
- [ ] Return `A001`; confirm status `returned`.
- [ ] Restart the application and confirm the request persists.

## Validation and failure cases

- [ ] Create a request with a fellow ID surrounded by spaces; confirm the stored value is trimmed.
- [ ] Try a whitespace-only fellow ID; confirm rejection and no ID is consumed.
- [ ] Try an unsupported card type; confirm rejection.
- [ ] Try issuing a requested card; confirm rejection and unchanged record.
- [ ] Try approving a request with a blank approver; confirm rejection and unchanged record.
- [ ] Try returning a card before it is issued; confirm rejection.
- [ ] Try a second approval, issue, or return after the request has moved past that state; confirm rejection.
- [ ] Corrupt a copy of the JSON file and attempt to load it; confirm a clear error and unchanged in-memory records.
- [ ] Save a valid file, then simulate an invalid save input; confirm the valid destination contents remain unchanged.
- [ ] Load records with IDs `A001` and `A005`; confirm the next generated ID is `A006`.

## Evidence to capture

Record the actual commands, output, and test results from your run. Do not mark a scenario complete until it has been performed and observed.
