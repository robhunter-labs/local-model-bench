# Secure configuration baseline

Each control maps to the threats it addresses and to the check that proves it. Status is honest: most of this is not verified yet.

| Status | Meaning |
| --- | --- |
| `observed` | Seen once on the real host, October 2026 |
| `configured-unverified` | Set per the setup guide; not independently checked since |
| `built-not-exercised` | Exists in this repo, passes its own tests, not run against the real host or model |
| `planned` | Not done |

<!-- BEGIN GENERATED -->
| ID | Control | How it's checked | Status | Threats |
| --- | --- | --- | --- | --- |
| C01 | Model server listens on loopback only | NE-01 on the host after every reboot or update | `observed` | T01 |
| C02 | Host firewall admits SSH only | P01 scan from another device on the network | `configured-unverified` | T01, T11 |
| C03 | SSH key-only login, password auth off, host key verified on first use | P03 configuration review | `configured-unverified` | T02, T11 |
| C04 | Dedicated non-admin account on the host, full-disk encryption on | P05 host review | `configured-unverified` | T06, T07 |
| C05 | Runtime cloud features disabled | NE-02 on the host | `observed` | T13 |
| C06 | One model, tag and digest recorded; no silent re-pull | AU-03 compares served model to the recorded pin | `observed` | T03, T12 |
| C07 | Weights vetted before use: provenance, digest, card, licence, behaviour canaries | P10 using setup/WEIGHTS.md | `planned` | T03 |
| C08 | No secrets, keys or source on the host | DL-03 names-only inventory, P05 | `planned` | T07 |
| C09 | Single model, single request, context and output caps, client timeouts | RL-01..RL-03 | `observed` | T09 |
| C10 | Harness tools default-deny with an explicit allowlist | HP-01, HP-03 | `built-not-exercised` | T03, T04, T08, T10 |
| C11 | Harness enforces one call at a time where sequencing matters | HP-02, HP-05 | `built-not-exercised` | T10, T14 |
| C12 | Tool results fenced and marked untrusted before the model sees them | HP-04, PI-01..PI-03 | `built-not-exercised` | T04, T08 |
| C13 | Every request and response recorded with hashes, settings and timing | LG-01 | `built-not-exercised` | T05 |
| C14 | Tools run in a sandbox with no network egress by default | P08, P09 | `planned` | T03, T08 |
| C15 | Advisory only: a person decides every real effect | Policy; no tools attached during the October runs | `observed` | T04, T10, T14 |
| C16 | Tunnel key restricted to one forward, no shell, no agent forwarding | P04 | `planned` | T01, T11, T15 |
| C17 | Host logs protected and retained on purpose, not by default | DL-02, LG-02 | `planned` | T05, T06 |
| C18 | Named updates only; rerun host checks after any update | Change log plus NE-01, NE-02, AU-03 | `configured-unverified` | T12 |
| C19 | Only chat and model-list paths reachable through the tunnel (small proxy) | AU-04, P06 | `planned` | T15 |
<!-- END GENERATED -->

## Reference settings (from the host checklist)

```sh
# Ollama on macOS, set for the app's environment, then restart the app
launchctl setenv OLLAMA_NO_CLOUD 1
launchctl setenv OLLAMA_HOST "127.0.0.1:11434"
launchctl setenv OLLAMA_CONTEXT_LENGTH 8192
launchctl setenv OLLAMA_MAX_LOADED_MODELS 1
launchctl setenv OLLAMA_NUM_PARALLEL 1
```

Remote access to the inference port is a restricted tunnel to that port only (C16, `planned`). Key and tunnel configuration are deliberately not published here.

Environment settings may not survive a logout or reboot. Re-run NE-01 and NE-02 after either, and after any update (C18).
