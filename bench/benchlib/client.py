"""Minimal OpenAI-compatible client (standard library only).

Works with any server exposing /v1/chat/completions and /v1/models, such as Ollama's
compatibility layer. The api_key is sent only because some servers insist on the field;
for a local Ollama server it is not access control.
"""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request

LOOPBACK = {"127.0.0.1", "localhost", "::1"}
# Loopback traffic must never go through an HTTP proxy (http_proxy/https_proxy on corporate
# laptops would otherwise carry bench prompts and planted data off the host, untested).
_NO_PROXY = urllib.request.build_opener(urllib.request.ProxyHandler({}))


class EndpointError(Exception):
    pass


class Client:
    def __init__(self, base_url: str, model: str, api_key: str | None = "placeholder", timeout: float = 60.0):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key
        self.timeout = timeout

    def _request(self, method: str, path: str, body: dict | None = None, api_key: str | None = "__default__"):
        key = self.api_key if api_key == "__default__" else api_key
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(self.base_url + path, data=data, method=method)
        req.add_header("Content-Type", "application/json")
        if key:
            req.add_header("Authorization", f"Bearer {key}")
        started = time.monotonic()
        try:
            host = urllib.parse.urlsplit(self.base_url).hostname or ""
            opener = _NO_PROXY if host in LOOPBACK else urllib.request.build_opener()
            with opener.open(req, timeout=self.timeout) as resp:
                raw = resp.read()
                status = resp.status
        except urllib.error.HTTPError as e:
            raw, status = e.read(), e.code
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            raise EndpointError(str(e)) from e
        elapsed = time.monotonic() - started
        try:
            payload = json.loads(raw.decode() or "null")
        except json.JSONDecodeError:
            payload = {"_unparsed": raw.decode(errors="replace")[:2000]}
        return status, payload, elapsed

    def models(self, api_key: str | None = "__default__"):
        return self._request("GET", "/models", api_key=api_key)

    def chat(self, messages, tools=None, max_tokens=512, temperature=0, extra=None, api_key="__default__"):
        body = {"model": self.model, "messages": messages, "max_tokens": max_tokens,
                "temperature": temperature, "stream": False}
        if tools:
            body["tools"] = tools
        if extra:
            body.update(extra)
        return self._request("POST", "/chat/completions", body, api_key=api_key)


class FakeClient:
    """Deterministic stand-in used by --dry-run. Returns each case's declared fixture.

    Dry-run results prove the plumbing, scoring and guard work. They say nothing about a model.
    """

    def __init__(self, model: str = "dry-run-fixture"):
        self.model = model
        self.base_url = "dry-run://"
        self._next = None

    def prime(self, response):
        self._next = response

    def models(self, api_key="__default__"):
        return 200, {"data": [{"id": self.model}]}, 0.0

    def chat(self, messages, tools=None, max_tokens=512, temperature=0, extra=None, api_key="__default__"):
        resp = self._next or {"content": ""}
        msg = {"role": "assistant", "content": resp.get("content", "")}
        if resp.get("tool_calls"):
            msg["tool_calls"] = [
                {"id": f"call_{i}", "type": "function",
                 "function": {"name": c["name"], "arguments": json.dumps(c.get("arguments", {}))}}
                for i, c in enumerate(resp["tool_calls"])]
        usage = {"prompt_tokens": 0, "completion_tokens": resp.get("completion_tokens", 8)}
        return 200, {"choices": [{"message": msg, "finish_reason": "stop"}], "usage": usage}, 0.0
