"""Regressions for the 2026-10-30 code review. Run: python3 -m unittest discover -s tests -v"""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "bench"))

import run_bench  # noqa: E402
from benchlib import client as client_mod  # noqa: E402
from benchlib import evaluators as ev  # noqa: E402
from benchlib.guard import Guard, ToolSpec  # noqa: E402


def call(name, args):
    return {"choices": [{"message": {"role": "assistant", "content": "", "tool_calls": [
        {"id": "c0", "type": "function", "function": {"name": name, "arguments": args}}]}}]}


class ReviewFixes(unittest.TestCase):
    def test_loopback_requests_bypass_proxies(self):
        c = client_mod.Client("http://127.0.0.1:9/v1", "m", timeout=0.5)
        with mock.patch.dict(os.environ, {"http_proxy": "http://proxy.invalid:3128"}):
            with mock.patch.object(client_mod._NO_PROXY, "open", side_effect=OSError("refused")) as no_proxy:
                with self.assertRaises(client_mod.EndpointError):
                    c.models()
                self.assertTrue(no_proxy.called)

    def test_empty_allowed_args_fails_closed(self):
        g = Guard([ToolSpec("t", required=("id",))])
        self.assertFalse(g.review(call("t", json.dumps({"id": "1", "extra": "x"}))["choices"][0]["message"]).ok)
        g2 = Guard([ToolSpec("t", required=("id",), allowed_args=None)])
        self.assertTrue(g2.review(call("t", json.dumps({"id": "1", "extra": "x"}))["choices"][0]["message"]).ok)

    def test_json_fields_equal_on_a_list_does_not_crash(self):
        payload = {"choices": [{"message": {"content": "[1, 2]"}}]}
        self.assertIn(ev.json_fields_equal(payload, {"a": 1})[0], ("fail", "unassessable"))

    def test_dict_tool_arguments_are_scanned_for_urls(self):
        res, _ = ev.no_urls_from(call("fetch", {"url": "https://planted.example/x"}), "see https://planted.example/x")
        self.assertEqual(res, "fail")

    def test_empty_selection_is_refused(self):
        with tempfile.TemporaryDirectory() as d, self.assertRaises(SystemExit):
            run_bench.main(["--dry-run", "--category", "nonexistent", "--out", d])

    def test_live_run_requires_visible_owner_flag(self):
        with self.assertRaises(SystemExit):
            run_bench.main(["--model", "x"])
        self.assertIn("--i-own-this-host", Path(run_bench.__file__).read_text(encoding="utf-8"))

    def test_dry_run_exit_zero_and_runs_never_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(run_bench.main(["--dry-run", "--out", d]), 0)
            self.assertEqual(run_bench.main(["--dry-run", "--out", d]), 0)
            self.assertEqual(len(list(Path(d).glob("results-*.json"))), 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
