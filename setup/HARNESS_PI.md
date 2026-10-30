# Harness: Pi (planned)

**Status: planned.** The October runs used a hand-built harness, not Pi. This is how I'd wire Pi to the tunnelled model, and where the enforced rules would go.

## 1. Point Pi at the tunnel

`~/.pi/agent/models.json` (see `pi-models.example.json` here):

```json
{
  "providers": {
    "local-bench": {
      "baseUrl": "http://127.0.0.1:LOCAL_PORT/v1",
      "api": "openai-completions",
      "apiKey": "placeholder-not-a-lock",
      "models": [{ "id": "YOUR_PINNED_MODEL_TAG", "contextWindow": 16384 }]
    }
  }
}
```

Field names follow Pi's custom-models documentation at the time of writing; check the current docs before relying on them.

## 2. Tell the model the rules (the playbook)

`AGENTS.md` (see `AGENTS.example.md`) carries the advisory-only rules. That's the part that *asks*.

## 3. Enforce the rules (the harness)

Pi has no built-in permission prompts. Its documentation suggests running it in a container or adding a confirmation flow with extensions, and it ships example extensions for a permission gate and protected paths. The plan:

| Rule | Where it's enforced | Bench case |
| --- | --- | --- |
| Default-deny tools; explicit allowlist | extension, same logic as `bench/benchlib/guard.py` | HP-01, HP-03 |
| One call at a time where sequencing matters | extension | HP-02, HP-05 |
| Tool results fenced as untrusted | extension wraps results | HP-04, PI-01..PI-03 |
| No network egress from tools | container with networking off | P08, P09 |
| No host filesystem beyond a scratch directory | container mount | P08 |
| A person approves every effect | confirmation flow | C15 |

The guard in this repo is the reference behaviour. The Pi extension should pass the same cases when its tool decisions are fed through `run_bench.py`.

## 4. Rerun the failures

The point of all this: rerun the sequencing case (HP-05) and the authorization-versus-compromise case (RE-02) *through* the harness, and record model compliance and guard enforcement separately.
