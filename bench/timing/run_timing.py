#!/usr/bin/env python3
"""Small, repeatable cost bench for a local Ollama model.

Standard library only. Runs prompts through Ollama on this machine and saves
timings and configuration without writing the prompt or answer text.

What it records, per call: load, prompt-reading and answer-writing time and
token counts (from Ollama's own response fields), the context size used, and
where the loaded model sat (GPU share, from /api/ps). Once per run it records
the installed model size and the free disk space, on their own line, apart
from the speed numbers.

Example:
  python3 bench/timing/run_timing.py --i-own-this-host --model qwen3.6:27b --prompts bench/timing/sample_prompts.jsonl \
      --repeats 2 --num-ctx 4096 8192 --out runs/my-run.jsonl
"""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import sys
import time
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener


class NoRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


OPENER = build_opener(ProxyHandler({}), NoRedirects())


def loopback_address(value):
    parsed = urlsplit(value)
    if (parsed.scheme != "http" or parsed.hostname not in {"localhost", "127.0.0.1", "::1"}
            or parsed.username or parsed.password or parsed.path not in {"", "/"}
            or parsed.query or parsed.fragment):
        raise argparse.ArgumentTypeError("use a plain loopback HTTP address for Ollama")
    return value.rstrip("/")

def call(base, path, body=None, timeout=600):
    data = None if body is None else json.dumps(body).encode()
    req = Request(base + path, data=data, headers={"Content-Type": "application/json"})
    with OPENER.open(req, timeout=timeout) as r:
        return json.loads(r.read().decode())

def installed_bytes(base, model):
    for m in call(base, "/api/tags").get("models", []):
        if m.get("name") == model or m.get("model") == model:
            return m.get("size"), m.get("digest")
    return None, None

def placement(base, model):
    for m in call(base, "/api/ps").get("models", []):
        if m.get("name") == model or m.get("model") == model:
            size, vram = m.get("size") or 0, m.get("size_vram") or 0
            return {"loaded_bytes": size, "gpu_bytes": vram,
                    "gpu_share": round(vram / size, 3) if size else None}
    return {"loaded_bytes": None, "gpu_bytes": None, "gpu_share": None}

def unload(base, model):
    # keep_alive 0 asks Ollama to unload the model, so the next call is a cold load.
    call(base, "/api/generate", {"model": model, "keep_alive": 0})

def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--base", type=loopback_address, default="http://127.0.0.1:11434")
    ap.add_argument("--model", required=True)
    ap.add_argument("--prompts", required=True, help="JSONL, one {\"id\":..., \"prompt\":...} per line")
    ap.add_argument("--repeats", type=int, default=2)
    ap.add_argument("--num-ctx", type=int, nargs="+", default=[4096])
    ap.add_argument("--num-predict", type=int, default=192)
    ap.add_argument("--temperature", type=float, default=0.2)
    ap.add_argument("--seed", type=int, default=41)
    ap.add_argument("--keep-alive", default="1m")
    ap.add_argument("--models-dir", default=os.getenv("OLLAMA_MODELS") or os.path.expanduser("~/.ollama/models"),
                    help="folder whose disk the free-space reading is taken from")
    ap.add_argument("--cold-start", action="store_true", help="unload the model before each context size")
    ap.add_argument("--out", required=True)
    ap.add_argument("--i-own-this-host", action="store_true",
                    help="confirm you own this machine or are authorized to test it")
    a = ap.parse_args()
    if not a.i_own_this_host:
        ap.error("live runs need --i-own-this-host: run this only on a machine you own or are authorized to test")

    if a.repeats < 1 or a.num_predict < 1 or any(ctx < 1 for ctx in a.num_ctx):
        ap.error("repeats, output limit and context sizes must be positive")
    prompts = [json.loads(line) for line in Path(a.prompts).read_text().splitlines() if line.strip()]
    if not prompts or any(not isinstance(p, dict) or not re.fullmatch(r"[A-Za-z0-9_-]{1,48}", str(p.get("id", "")))
                         or not isinstance(p.get("prompt"), str) or not p["prompt"].strip() for p in prompts):
        ap.error("provide at least one nonempty prompt with a short, non-sensitive ID")
    if len({p["id"] for p in prompts}) != len(prompts):
        ap.error("prompt IDs must be unique")
    out_path = Path(a.out)
    if out_path.exists():
        ap.error("output already exists; choose a new path for this run")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    size, digest = installed_bytes(a.base, a.model)
    if digest is None:
        ap.error("model not found in this Ollama instance's installed model list")
    du = shutil.disk_usage(a.models_dir) if os.path.isdir(a.models_dir) else None
    version = call(a.base, "/api/version").get("version")
    with out_path.open("x") as out:
        out.write(json.dumps({"kind": "storage", "model": a.model, "digest": digest,
                              "installed_bytes": size, "free_bytes": du.free if du else None,
                              "disk_total_bytes": du.total if du else None, "ollama_version": version,
                              "num_ctx": a.num_ctx, "num_predict": a.num_predict, "temperature": a.temperature,
                              "seed": a.seed, "keep_alive": a.keep_alive, "think": False,
                              "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}) + "\n")
        out.flush()
        order = 0
        for context_block, ctx in enumerate(a.num_ctx, start=1):
            if a.cold_start:
                unload(a.base, a.model)
            for rep in range(1, a.repeats + 1):
                for p in prompts:
                    order += 1
                    body = {"model": a.model, "prompt": p["prompt"], "stream": False,
                            "think": False, "keep_alive": a.keep_alive,
                            "options": {"num_ctx": ctx, "num_predict": a.num_predict,
                                        "temperature": a.temperature, "seed": a.seed}}
                    t0 = time.perf_counter()
                    r = call(a.base, "/api/generate", body)
                    wall = time.perf_counter() - t0
                    ns = 1e9
                    rec = {"kind": "call", "order": order, "prompt_id": p.get("id"), "repeat": rep,
                           "num_ctx": ctx, "context_block": context_block, "wall_s": round(wall, 3),
                           "load_s": r["load_duration"] / ns,
                           "prompt_tokens": r.get("prompt_eval_count"),
                           "cached_prompt_tokens": r.get("prompt_eval_cached_count"),
                           "prompt_s": r["prompt_eval_duration"] / ns,
                           "output_tokens": r.get("eval_count"),
                           "output_s": r["eval_duration"] / ns,
                           "total_s": r["total_duration"] / ns,
                           "done_reason": r.get("done_reason")}
                    rec.update(placement(a.base, a.model))
                    out.write(json.dumps(rec) + "\n"); out.flush()
                    print(f"{order:>3} ctx={ctx} {p.get('id')} r{rep}: "
                          f"{rec['output_tokens'] or 0}/{rec['output_s']:.2f}s, load {rec['load_s']:.2f}s",
                          file=sys.stderr)
        out.write(json.dumps({"kind": "complete", "calls": order}) + "\n")

if __name__ == "__main__":
    main()
