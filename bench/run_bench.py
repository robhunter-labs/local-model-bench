#!/usr/bin/env python3
"""Run the method bank.

  python3 bench/run_bench.py --dry-run
  python3 bench/run_bench.py --base-url http://127.0.0.1:11434/v1 --model TAG --out results/local/

Dry-run results are synthetic fixtures. They prove the plumbing, guard and scorers,
not anything about a model or host, and every record says so.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from benchlib.client import Client, EndpointError, FakeClient  # noqa: E402
from benchlib.evaluators import EVALUATORS  # noqa: E402
from benchlib.guard import Guard, ToolSpec  # noqa: E402
from benchlib import host_checks  # noqa: E402

TYPES = {"str": str, "int": int, "float": float, "bool": bool}


def sha(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=str).encode()).hexdigest()


def load_cases(methods_dir: Path, category=None, case_id=None):
    cases = []
    for f in sorted(methods_dir.glob("*.json")):
        bank = json.loads(f.read_text())
        for c in bank["cases"]:
            if category and c["category"] != category:
                continue
            if case_id and c["id"] != case_id:
                continue
            cases.append(c)
    return cases


def guard_from(specs):
    return Guard([ToolSpec(name=s["name"], required=tuple(s.get("required", ())), allowed_args=tuple(s.get("allowed_args", ())),
                           arg_types={k: TYPES[v] for k, v in s.get("arg_types", {}).items()}) for s in specs])


def wrap_messages(messages):
    out = []
    for m in messages:
        if m.get("role") == "tool":
            m = dict(m, content=Guard.wrap_result(m.get("tool_call_id", "?"), m["content"]))
        out.append(m)
    return out


def run_case(case, client, dry: bool, pin: str | None):
    kind = case["kind"]
    rec = {"case_id": case["id"], "category": case["category"], "title": case["title"], "kind": kind,
           "threats": case.get("threats", []), "synthetic_dry_run": dry,
           "started_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}
    request, response, t0 = None, None, time.monotonic()

    if kind == "host":
        request = {"check": case["check"], "args": case.get("args", {})}
        obs = case["dry_run_observation"] if dry else host_checks.CHECKS[case["check"]](**case.get("args", {}))
        response = obs
        rec["result"], rec["detail"] = obs["result"], obs["detail"]

    elif kind == "manual":
        request = {"steps": case["steps"]}
        rec["result"], rec["detail"] = "manual", f"operator steps ({case.get('run_where', 'anywhere')}): " + " | ".join(case["steps"])

    elif kind == "endpoint":
        op = case["op"]
        request = {"op": op}
        try:
            if dry:
                obs = case["dry_run_observation"]
                status, payload = obs["status"], {"data": [{"id": i} for i in obs.get("ids", [client.model])]}
            elif op == "models_no_key":
                status, payload, _ = client.models(api_key=None)
            elif op == "models_bogus_key":
                status, payload, _ = client.models(api_key="bench-not-a-real-key")
            elif op == "model_pinned":
                status, payload, _ = client.models()
            elif op == "admin_namespace_reachable":
                root = client.base_url[:-3] if client.base_url.endswith("/v1") else client.base_url
                c2 = Client(root, client.model, timeout=client.timeout)
                status, payload, _ = c2._request("GET", "/api/tags")  # read-only listing
            else:
                raise ValueError(op)
            reachable = status == 200
        except EndpointError as e:
            status, payload, reachable = None, {"error": str(e)}, False
        response = {"status": status}
        if op == "model_pinned":
            ids = [m.get("id") for m in (payload or {}).get("data", [])]
            want = pin or client.model
            rec["result"] = "pass" if want in ids else "fail"
            rec["detail"] = f"pinned {want!r} {'served' if want in ids else 'not in served list'}"
            response["ids"] = ids
        else:
            expect = case.get("expect", "reachable")
            if expect == "reachable":
                rec["result"] = "finding" if reachable else "pass"
                rec["detail"] = ("reachable without a real credential; " + case["interpretation"]) if reachable else "not reachable"
            else:
                rec["result"] = "fail" if reachable else "pass"
                rec["detail"] = "management namespace reachable through this path" if reachable else "management namespace not reachable"

    elif kind in ("model", "model_guard"):
        msgs = wrap_messages(case["messages"]) if case.get("wrap_tool_results") else case["messages"]
        request = {"messages": msgs, "tools": case.get("tools"), "max_tokens": case.get("max_tokens", 512)}
        if dry:
            client.prime(case["dry_run_response"])
        try:
            status, payload, _ = client.chat(msgs, tools=case.get("tools"), max_tokens=case.get("max_tokens", 512))
        except EndpointError as e:
            status, payload = None, {"error": str(e)}
        response = payload
        if status != 200:
            rec["result"], rec["detail"] = "error", f"HTTP {status}: {str(payload)[:200]}"
        elif kind == "model":
            ev = case["evaluator"]
            rec["result"], rec["detail"] = EVALUATORS[ev["name"]](payload, **ev.get("args", {}))
        else:
            msg = payload["choices"][0]["message"]
            n = len(msg.get("tool_calls") or [])
            decision = guard_from(case["guard_tools"]).review(msg)
            guard_ok = (n <= 1 and decision.ok) or (n > 1 and not decision.ok)
            rec["model_compliance"] = "pass" if n == 1 else f"fail: {n} calls in one response"
            rec["guard_enforcement"] = "pass" if guard_ok else "fail"
            rec["result"] = "pass" if guard_ok else "fail"
            rec["detail"] = f"guard {'held' if guard_ok else 'did not hold'}; model compliance: {rec['model_compliance']}"

    elif kind == "guard":
        decision = guard_from(case["tools"]).review(case["model_message"])
        reasons = [r for _, r in decision.rejected]
        want = case["expect"]
        ok = decision.ok == want["ok"] and (not want.get("reason_contains") or any(want["reason_contains"] in r for r in reasons))
        request, response = {"model_message": case["model_message"]}, {"ok": decision.ok, "reasons": reasons}
        rec["result"], rec["detail"] = ("pass" if ok else "fail"), (f"rejected: {reasons}" if reasons else "allowed")

    elif kind == "guard_wrap":
        wrapped = Guard.wrap_result("c1", case["result_text"])
        closes = wrapped.count("<<END_UNTRUSTED_TOOL_RESULT")
        ok = closes == 1 and wrapped.rstrip().endswith(">>") and "not an instruction" in wrapped
        request, response = {"result_text": case["result_text"]}, {"wrapped": wrapped}
        rec["result"], rec["detail"] = ("pass" if ok else "fail"), f"fence closes {closes} time(s)"

    elif kind == "timeout":
        filler = "synthetic-record " * case["filler_tokens_approx"]
        msgs = [{"role": "user", "content": filler + "\nCount the records."}]
        request = {"approx_tokens": case["filler_tokens_approx"], "timeout_s": case["timeout_s"]}
        if dry:
            rec["result"], rec["detail"] = "pass", "fixture: client stopped at budget"
            response = {"timed_out": True}
        else:
            c2 = Client(client.base_url, client.model, timeout=case["timeout_s"])
            try:
                c2.chat(msgs, max_tokens=16)
                rec["result"], rec["detail"] = "inconclusive", "completed inside the budget; raise filler size"
                response = {"timed_out": False}
            except EndpointError:
                rec["result"], rec["detail"] = "pass", "client stopped at budget; " + case["interpretation"]
                response = {"timed_out": True}

    elif kind == "selfcheck":
        rec["result"], rec["detail"] = "deferred", "checked after the run against the written records"
    else:
        rec["result"], rec["detail"] = "error", f"unknown kind {kind}"

    rec["elapsed_s"] = round(time.monotonic() - t0, 3)
    rec["settings"] = {"base_url": client.base_url, "model": client.model, "max_tokens": case.get("max_tokens")}
    rec["request_sha256"], rec["response_sha256"] = sha(request), sha(response)
    return rec, request, response


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base-url", default="http://127.0.0.1:11434/v1")
    ap.add_argument("--model", default=None, help="the exact pinned tag you serve")
    ap.add_argument("--pin", default=None, help="tag expected in the served list (defaults to --model)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--i-own-this-host", dest="owner_ack", action="store_true", help=argparse.SUPPRESS)
    ap.add_argument("--category")
    ap.add_argument("--case")
    ap.add_argument("--timeout", type=float, default=120)
    ap.add_argument("--out", default=None)
    ap.add_argument("--methods", default=str(HERE / "methods"))
    a = ap.parse_args(argv)

    if not a.dry_run and not a.model:
        ap.error("--model is required unless --dry-run")
    if not a.dry_run and not a.owner_ack:
        ap.error("live runs only touch hosts you own; this bench won't start until you say so (read the source)")
    client = FakeClient() if a.dry_run else Client(a.base_url, a.model, timeout=a.timeout)
    cases = load_cases(Path(a.methods), a.category, a.case)
    out = Path(a.out) if a.out else (HERE.parent / "results" / ("dry-run" if a.dry_run else "local"))
    out.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    records = []
    with open(out / f"requests-{stamp}.jsonl", "w") as raw:
        for c in cases:
            rec, req, resp = run_case(c, client, a.dry_run, a.pin)
            raw.write(json.dumps({"case_id": c["id"], "request": req, "response": resp}, default=str) + "\n")
            records.append(rec)
            print(f"{rec['case_id']:6} {rec['result']:12} {rec['title']}")
    # LG-01: every record must carry the logging fields
    for c in cases:
        if c["kind"] == "selfcheck":
            missing = [(r["case_id"], f) for r in records if r["kind"] != "selfcheck" for f in c["required_fields"] if f not in r]
            for r in records:
                if r["case_id"] == c["id"]:
                    r["result"] = "fail" if missing else "pass"
                    r["detail"] = f"missing fields: {missing[:5]}" if missing else f"{len(records) - 1} records complete"
                    print(f"{r['case_id']:6} {r['result']:12} {r['title']} (post-run)")
    summary = {"schema": "local-model-bench/result/v1", "synthetic_dry_run": a.dry_run, "generated_utc": stamp,
               "counts": {k: sum(1 for r in records if r["result"] == k) for k in sorted({r["result"] for r in records})},
               "records": records}
    (out / f"results-{stamp}.json").write_text(json.dumps(summary, indent=1, default=str))
    print(f"\n{len(records)} cases -> {out}/results-{stamp}.json  {summary['counts']}")
    if a.dry_run:
        print("Dry run: synthetic fixtures only. Nothing here describes a real model or host.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
