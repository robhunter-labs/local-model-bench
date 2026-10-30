import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
T = json.loads((ROOT / "pentest" / "traceability.json").read_text())
BANK = {c["id"]: c for f in (ROOT / "bench" / "methods").glob("*.json") for c in json.loads(f.read_text())["cases"]}
STATUSES = set(T["status_vocabulary"])


class TraceabilityTests(unittest.TestCase):
    def test_every_threat_has_control_and_test_or_accepted_gap(self):
        gaps = {g["threat"] for g in T["accepted_gaps"]}
        for th in T["threats"]:
            if th["id"] in gaps:
                continue
            self.assertTrue(th["controls"], f"{th['id']} has no control")
            self.assertTrue(th["bench"] or th["pentest"], f"{th['id']} has no test")

    def test_references_resolve(self):
        controls = {c["id"] for c in T["controls"]}
        methods = {p["id"] for p in T["pentest"]}
        for th in T["threats"]:
            self.assertTrue(set(th["controls"]) <= controls, th["id"])
            self.assertTrue(set(th["pentest"]) <= methods, th["id"])
            self.assertTrue(set(th["bench"]) <= set(BANK), (th["id"], set(th["bench"]) - set(BANK)))

    def test_every_control_and_method_is_used(self):
        used_c = {c for th in T["threats"] for c in th["controls"]}
        used_p = {p for th in T["threats"] for p in th["pentest"]}
        self.assertEqual(used_c, {c["id"] for c in T["controls"]})
        self.assertEqual(used_p, {p["id"] for p in T["pentest"]})

    def test_bench_case_threats_agree_with_threat_table(self):
        for cid, c in BANK.items():
            for tid in c["threats"]:
                th = next(t for t in T["threats"] if t["id"] == tid)
                self.assertIn(cid, th["bench"], f"{cid} claims {tid} but {tid} doesn't list it")

    def test_statuses_are_from_vocabulary(self):
        for c in T["controls"]:
            self.assertIn(c["status"], STATUSES, c["id"])

    def test_generated_docs_are_current(self):
        r = subprocess.run([sys.executable, str(ROOT / "tools" / "render_docs.py"), "--check"], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


if __name__ == "__main__":
    unittest.main()
