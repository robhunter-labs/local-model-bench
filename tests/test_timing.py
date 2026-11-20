"""Timing runner and summarizer tests. Run: python3 -m unittest discover -s tests -v

The runner is exercised against a fake Ollama server on loopback. No model,
weights or network access are needed.
"""
import json
import subprocess
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "bench" / "timing" / "run_timing.py"
SUMMARIZER = ROOT / "bench" / "timing" / "summarize_timing.py"
PROMPTS = ROOT / "bench" / "timing" / "sample_prompts.jsonl"
RECORDED = ROOT / "results" / "2026-10-21-timing" / "per_call.csv"
MODEL = "fake-model:1b"
NS = 1_000_000_000


class FakeOllama(BaseHTTPRequestHandler):
    requests = []

    def log_message(self, *args):
        pass

    def reply(self, body):
        data = json.dumps(body).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == "/api/tags":
            self.reply({"models": [{"name": MODEL, "size": 123456789, "digest": "sha256:abc"}]})
        elif self.path == "/api/version":
            self.reply({"version": "0.0.0-test"})
        elif self.path == "/api/ps":
            self.reply({"models": [{"name": MODEL, "size": 1000, "size_vram": 1000}]})
        else:
            self.send_error(404)

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        FakeOllama.requests.append(body)
        if body.get("keep_alive") == 0 and "prompt" not in body:
            self.reply({"done": True})
            return
        self.reply({"response": "SECRET-REPLY-TEXT", "done_reason": "stop",
                    "load_duration": int(0.2 * NS), "prompt_eval_count": 40,
                    "prompt_eval_duration": int(0.25 * NS), "eval_count": 21,
                    "eval_duration": int(1.0 * NS), "total_duration": int(1.5 * NS)})


class TimingRunner(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = HTTPServer(("127.0.0.1", 0), FakeOllama)
        cls.base = f"http://127.0.0.1:{cls.server.server_address[1]}"
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()

    def setUp(self):
        FakeOllama.requests.clear()
        self.tmp = tempfile.TemporaryDirectory()
        self.out = Path(self.tmp.name) / "run.jsonl"

    def tearDown(self):
        self.tmp.cleanup()

    def run_bench(self, *extra, own=True):
        args = [sys.executable, str(RUNNER), "--base", self.base, "--model", MODEL,
                "--prompts", str(PROMPTS), "--repeats", "1", "--out", str(self.out),
                "--models-dir", self.tmp.name, *extra]
        if own:
            args.append("--i-own-this-host")
        return subprocess.run(args, capture_output=True, text=True, timeout=60)

    def test_live_run_needs_host_acknowledgement(self):
        proc = self.run_bench(own=False)
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("--i-own-this-host", proc.stderr)
        self.assertFalse(self.out.exists())
        self.assertEqual(FakeOllama.requests, [])

    def test_non_loopback_address_is_refused(self):
        args = [sys.executable, str(RUNNER), "--base", "http://192.0.2.1:11434", "--model", MODEL,
                "--prompts", str(PROMPTS), "--out", str(self.out), "--i-own-this-host"]
        proc = subprocess.run(args, capture_output=True, text=True, timeout=60)
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("loopback", proc.stderr)

    def test_run_records_settings_and_timings_without_text(self):
        proc = self.run_bench("--num-ctx", "4096", "8192", "--cold-start")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        records = [json.loads(line) for line in self.out.read_text().splitlines()]
        storage, calls, complete = records[0], records[1:-1], records[-1]
        prompts = [json.loads(line) for line in PROMPTS.read_text().splitlines() if line.strip()]
        self.assertEqual(storage["kind"], "storage")
        self.assertEqual(storage["installed_bytes"], 123456789)
        self.assertEqual(storage["num_ctx"], [4096, 8192])
        self.assertFalse(storage["think"])
        self.assertEqual(len(calls), 2 * len(prompts))
        self.assertEqual({c["context_block"] for c in calls}, {1, 2})
        self.assertEqual(complete, {"kind": "complete", "calls": len(calls)})
        for c in calls:
            self.assertAlmostEqual(c["load_s"], 0.2)
            self.assertAlmostEqual(c["output_s"], 1.0)
            self.assertEqual(c["gpu_share"], 1.0)
        generate = [r for r in FakeOllama.requests if "prompt" in r]
        self.assertTrue(all(r["think"] is False and r["options"]["num_predict"] == 192 for r in generate))
        self.assertEqual(len(FakeOllama.requests) - len(generate), 2)  # one unload per context block
        text = self.out.read_text()
        self.assertNotIn("SECRET-REPLY-TEXT", text)
        for p in prompts:
            self.assertNotIn(p["prompt"], text)

    def test_missing_storage_path_is_reported_as_unavailable(self):
        proc = self.run_bench("--models-dir", str(Path(self.tmp.name) / "absent"))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        storage = json.loads(self.out.read_text().splitlines()[0])
        self.assertIsNone(storage["free_bytes"])

    def test_existing_output_is_refused(self):
        self.out.write_text("keep me\n")
        proc = self.run_bench()
        self.assertNotEqual(proc.returncode, 0)
        self.assertEqual(self.out.read_text(), "keep me\n")


class RecordedRun(unittest.TestCase):
    def test_summary_reproduces_published_numbers(self):
        proc = subprocess.run([sys.executable, str(SUMMARIZER), str(RECORDED),
                               "--exclude-prompt-rate-orders", "30", "32"],
                              capture_output=True, text=True, timeout=60)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        for expected in ("| Calls | 32 |", "| First reported model-load time, s | 10.18 |",
                         "0.18 (0.17 to 0.32)", "20.8 (19.4 to 22.0)", "162 (132 to 177)",
                         "4.42 (1.95 to 12.79)", "| 135.5 |"):
            self.assertIn(expected, proc.stdout)

    def test_recorded_csv_holds_no_text_columns(self):
        header = RECORDED.read_text().splitlines()[0].split(",")
        self.assertFalse({"prompt", "response", "reply", "text"} & set(header))


if __name__ == "__main__":
    unittest.main()
