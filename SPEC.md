# Spec: a local inference bench I'd trust a little

## Purpose

Run one open-weight model locally for **advisory** help with authorized security work, and know, with evidence, what it can reach, what can reach it, and what it is allowed to do. The model is treated as untrusted code from a stranger, however useful it is.

## Scope

In scope:
- One inference host (a laptop) running one model through Ollama or another OpenAI-compatible server.
- One client machine reaching it over an SSH tunnel.
- One agent harness (Pi, or similar) on the client, with enforced rules.
- Synthetic tasks and fixtures only.

Out of scope, for now:
- Real targets, real credentials, real customer or work data.
- Unattended tool execution, remediation, or anything with an external effect.
- Fine-tuning or training (see [`setup/TRAINING.md`](setup/TRAINING.md)).
- Multi-user serving.

## Architecture

```text
 CLIENT MACHINE                                   INFERENCE HOST (dedicated account)
 ┌──────────────────────────────┐                 ┌───────────────────────────────────┐
 │ agent harness (Pi)           │                 │ Ollama  ── listens on 127.0.0.1    │
 │  ├─ guard: tool allowlist,   │  SSH tunnel     │   └─ one pinned model, cloud off   │
 │  │  one call at a time,      │ ═══════════════▶│ model files + logs (~/.ollama)    │
 │  │  results marked untrusted │  local forward  │ no source mounts, no secrets      │
 │  └─ base URL 127.0.0.1:PORT  │                 │ firewall: SSH only                │
 │ bench suite (this repo)      │                 └───────────────────────────────────┘
 └──────────────────────────────┘                          ▲ local network seat
                 ▲                                         │ (a foothold if compromised)
                 │ prompts, fixtures, results               │
             operator (decides every effect)
```

## Trust boundaries

| ID | Boundary | Why it matters |
| --- | --- | --- |
| TB1 | Network → inference server | Ollama has no real authentication. The listener must never leave loopback; the tunnel is the lock. |
| TB2 | Client → host account (SSH) | The client trusts the host's key and the host trusts the client's key. A compromised host is one hop from the client. |
| TB3 | Model output → harness | Output is untrusted text. Tool calls are proposals, not actions. |
| TB4 | Tool result → model context | Tool output is data, never instruction. |
| TB5 | Weights → runtime | Third-party weight edits may carry behaviour nobody disclosed. |
| TB6 | Host → local network | The host is a seat on the network, whatever it holds. |

## Success bar

The bench is "done enough to use for advisory work" when:
1. Every threat in [`threat-model/STRIDE.md`](threat-model/STRIDE.md) has at least one control and at least one test, or an explicit, accepted gap. (Checked by `tests/test_traceability.py`.)
2. The network-exposure and auth cases pass **on the real host** after every reboot or update.
3. The harness guard is in the path of every tool call, and the sequencing and injection cases pass **through the harness**, not just in the prompt.
4. A penetration test against the host and harness, per [`pentest/TEST_MAP.md`](pentest/TEST_MAP.md), has been run and its findings dispositioned.

None of the four is met today. See [`STATE.md`](STATE.md).
