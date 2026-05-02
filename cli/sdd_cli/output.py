from __future__ import annotations

import json


def print_response(data, format: str = "json") -> None:
    if format == "json":
        print(json.dumps(data, indent=2, ensure_ascii=False))
    elif format == "table":
        if isinstance(data, list):
            _print_list_table(data)
        elif isinstance(data, dict):
            _print_dict_table(data)
        else:
            print(data)


def _print_list_table(items: list) -> None:
    if not items:
        print("(empty)")
        return
    if not isinstance(items[0], dict):
        for item in items:
            print(item)
        return
    keys = list(items[0].keys())
    widths = {k: max(len(k), *(len(str(row.get(k, ""))) for row in items)) for k in keys}
    header = "  ".join(k.ljust(widths[k]) for k in keys)
    print(header)
    print("  ".join("-" * widths[k] for k in keys))
    for row in items:
        print("  ".join(str(row.get(k, "")).ljust(widths[k]) for k in keys))


def _print_dict_table(data: dict) -> None:
    if not data:
        print("(empty)")
        return
    max_key_len = max(len(str(k)) for k in data)
    for key, value in data.items():
        print(f"{str(key).ljust(max_key_len)}  {value}")
