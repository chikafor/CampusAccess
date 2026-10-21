"""Interactive command-line interface for Campus Access."""
from __future__ import annotations

import sys
from typing import Callable

from request_manager import DEFAULT_STORAGE_PATH, RequestManager


def _print_request(record: dict[str, object]) -> None:
    print(
        f"{record['id']} | fellow: {record['fellow_id']} | "
        f"type: {record['card_type']} | status: {record['status']} | "
        f"approved by: {record['approved_by'] or '-'}"
    )


def _save_after_change(manager: RequestManager) -> None:
    try:
        manager.save_requests()
    except OSError as exc:
        print(f"WARNING: change is in memory but could not be saved: {exc}")
    else:
        print(f"Saved to {DEFAULT_STORAGE_PATH}")


def _show_menu() -> None:
    print(
        "\nCampus Access\n"
        "1. Create request\n"
        "2. List requests\n"
        "3. View request\n"
        "4. Approve request\n"
        "5. Issue card\n"
        "6. Return card\n"
        "7. Save requests\n"
        "8. Reload requests\n"
        "0. Exit"
    )


def run_cli() -> int:
    manager = RequestManager()
    try:
        manager.load_requests()
    except (ValueError, OSError) as exc:
        print(f"ERROR: could not load {DEFAULT_STORAGE_PATH}: {exc}", file=sys.stderr)
        print("No data was overwritten. Fix or restore the JSON file before restarting.", file=sys.stderr)
        return 1

    print(f"Loaded {len(manager.list_requests())} request(s) from {DEFAULT_STORAGE_PATH}.")
    while True:
        _show_menu()
        try:
            choice = input("Choose an option: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting Campus Access.")
            return 0

        try:
            if choice == "1":
                fellow_id = input("Fellow ID: ")
                card_type = input("Card type (visitor/student/staff): ")
                record = manager.create_request(fellow_id, card_type)
                _print_request(record)
                _save_after_change(manager)
            elif choice == "2":
                records = manager.list_requests()
                if not records:
                    print("No requests found.")
                else:
                    for record in records:
                        _print_request(record)
            elif choice == "3":
                _print_request(manager.get_request(input("Request ID: ")))
            elif choice == "4":
                request_id = input("Request ID: ")
                approved_by = input("Approver ID: ")
                _print_request(manager.approve_request(request_id, approved_by))
                _save_after_change(manager)
            elif choice == "5":
                _print_request(manager.issue_card(input("Request ID: ")))
                _save_after_change(manager)
            elif choice == "6":
                _print_request(manager.return_card(input("Request ID: ")))
                _save_after_change(manager)
            elif choice == "7":
                manager.save_requests()
                print(f"Saved requests to {DEFAULT_STORAGE_PATH}.")
            elif choice == "8":
                manager.load_requests()
                print(f"Loaded {len(manager.list_requests())} request(s).")
            elif choice == "0":
                print("Exiting Campus Access.")
                return 0
            else:
                print("Please choose one of the listed options.")
        except (ValueError, OSError) as exc:
            print(f"Error: {exc}")


if __name__ == "__main__":
    raise SystemExit(run_cli())
