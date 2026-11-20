#!/usr/bin/env python3
"""Summarize JSONL from run_timing.py or the companion's historical CSV."""
import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from statistics import median


def read_records(path):
    with path.open(encoding="utf-8", newline="") as stream:
        if path.suffix.lower() == ".csv":
            return list(csv.DictReader(stream)), [], None
        records = [json.loads(line) for line in stream if line.strip()]
    calls = [r for r in records if r.get("kind") == "call"]
    storage = [r for r in records if r.get("kind") == "storage"]
    completed = bool(records and records[-1].get("kind") == "complete"
                     and records[-1].get("calls") == len(calls))
    return calls, storage, completed


def rates(rows, seconds_key, count_key, exclude=()):
    values = []
    for row in rows:
        if int(row["order"]) in exclude or not row.get(count_key):
            continue
        seconds = float(row[seconds_key])
        if seconds <= 0:
            continue
        count = float(row[count_key])
        if count_key == "prompt_tokens" and row.get("cached_prompt_tokens") is not None:
            count -= int(row["cached_prompt_tokens"])
        if count > 0:
            values.append(count / seconds)
    return values


def display_range(values, places=2):
    if not values:
        return "Unavailable"
    return f"{median(values):.{places}f} ({min(values):.{places}f} to {max(values):.{places}f})"


def summarize(calls, excluded):
    load = [float(row["load_s"]) for row in calls]
    prefill = [float(row["load_s"]) + float(row["prompt_s"]) for row in calls]
    total = [float(row["total_s"]) for row in calls]
    reading = rates(calls, "prompt_s", "prompt_tokens", excluded)
    writing = rates(calls, "output_s", "output_tokens")
    print("| Measure | Value |")
    print("|---|---|")
    print(f"| Calls | {len(calls)} |")
    print(f"| First reported model-load time, s | {load[0]:.2f} |")
    print(f"| Later reported model-load time, s | {display_range(load[1:])} |")
    print(f"| First load plus prompt evaluation, s | {prefill[0]:.2f} |")
    print(f"| Later load plus prompt evaluation, s | {display_range(prefill[1:])} |")
    print(f"| Output generation, tokens/s | {display_range(writing, 1)} |")
    print(f"| Prompt evaluation, tokens/s ({len(reading)} calls) | {display_range(reading, 0)} |")
    print(f"| Per-call model-side total, s | {display_range(total)} |")
    print(f"| Sum of reported per-call durations, s | {sum(total):.1f} |")
    print("\nLoad plus prompt evaluation is a server-side pre-generation estimate. "
          "This runner uses non-streaming requests and cannot measure first-token delivery to the client.")


def gb(value):
    return f"{value / 1e9:.1f} GB" if value is not None else "unavailable"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    parser.add_argument("--exclude-prompt-rate-orders", nargs="+", type=int, default=[])
    args = parser.parse_args()
    calls, storage, completed = read_records(args.run)
    if not calls:
        parser.error("no recorded model calls")
    if completed is False:
        print("Partial run. The output has no matching completion record.\n")
    groups = defaultdict(list)
    for row in calls:
        groups[(row.get("context_block", 1), row.get("num_ctx", "unavailable"))].append(row)
    for (block, context), group in groups.items():
        print(f"\n## Block {block} · requested context {context}\n")
        summarize(group, args.exclude_prompt_rate_orders)
    if args.exclude_prompt_rate_orders:
        orders = ", ".join(str(n) for n in args.exclude_prompt_rate_orders)
        print(f"\nCall numbers excluded from prompt-rate calculations only: {orders}.")
    for item in storage:
        print(f"\nStorage for {item['model']}: installed {gb(item.get('installed_bytes'))}, "
              f"free {gb(item.get('free_bytes'))}.")


if __name__ == "__main__":
    main()
