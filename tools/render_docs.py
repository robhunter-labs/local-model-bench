#!/usr/bin/env python3
"""Generate the threat, control and test-map tables from pentest/traceability.json and
the method bank, so the documents can't drift from the data. Run after editing either.
`python3 tools/render_docs.py --check` exits non-zero if a generated file is stale.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BEGIN, END = "<!-- BEGIN GENERATED -->", "<!-- END GENERATED -->"


def cases():
    out = {}
    for f in sorted((ROOT / "bench" / "methods").glob("*.json")):
        for c in json.loads(f.read_text())["cases"]:
            out[c["id"]] = c
    return out


def tables():
    t = json.loads((ROOT / "pentest" / "traceability.json").read_text())
    ctl = {c["id"]: c for c in t["controls"]}
    pt = {p["id"]: p for p in t["pentest"]}
    bank = cases()
    stride = ["| ID | STRIDE | Boundary | Threat | Controls | Bench cases | Pen-test methods |", "| --- | --- | --- | --- | --- | --- | --- |"]
    for th in t["threats"]:
        stride.append(f"| {th['id']} | {th['stride']} | {th['boundary']} | **{th['title']}.** {th['detail']} | {', '.join(th['controls'])} | {', '.join(th['bench'])} | {', '.join(th['pentest'])} |")
    base = ["| ID | Control | How it's checked | Status | Threats |", "| --- | --- | --- | --- | --- |"]
    for c in t["controls"]:
        threats = [th["id"] for th in t["threats"] if c["id"] in th["controls"]]
        base.append(f"| {c['id']} | {c['title']} | {c['check']} | `{c['status']}` | {', '.join(threats)} |")
    tm = ["| Method | What we try | Expect | Threats | Related bench cases |", "| --- | --- | --- | --- | --- |"]
    for p in t["pentest"]:
        threats = [th for th in t["threats"] if p["id"] in th["pentest"]]
        bench = sorted({b for th in threats for b in th["bench"]})
        tm.append(f"| {p['id']} | {p['title']} | {p['expect']} | {', '.join(th['id'] for th in threats)} | {', '.join(bench)} |")
    bankt = ["| Case | Category | Kind | What it checks | Threats |", "| --- | --- | --- | --- | --- |"]
    for cid, c in bank.items():
        bankt.append(f"| {cid} | {c['category']} | {c['kind']} | {c['title']} | {', '.join(c['threats'])} |")
    return {
        ROOT / "threat-model" / "STRIDE.md": "\n".join(stride),
        ROOT / "controls" / "BASELINE.md": "\n".join(base),
        ROOT / "pentest" / "TEST_MAP.md": "\n".join(tm),
        ROOT / "bench" / "METHOD_BANK.md": "\n".join(bankt),
    }


def splice(path, table):
    text = path.read_text()
    head, rest = text.split(BEGIN, 1)
    _, tail = rest.split(END, 1)
    return f"{head}{BEGIN}\n{table}\n{END}{tail}"


def main():
    check = "--check" in sys.argv
    stale = []
    for path, table in tables().items():
        new = splice(path, table)
        if path.read_text() != new:
            stale.append(path.relative_to(ROOT))
            if not check:
                path.write_text(new)
    if check and stale:
        print("stale:", *stale)
        return 1
    print("up to date" if check else f"rendered {len(tables())} files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
