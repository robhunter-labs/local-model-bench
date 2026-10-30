# Weights: reference only

No weights are included here, and nothing in this repo downloads any.

## What I ran in October

A community **refusal-reduced derivative of a Qwen mixture-of-experts model, about 35 billion parameters (roughly 3 billion active), Q8_0 quantization, about 39 GB**, served by Ollama. The exact tag and digest are recorded privately.

## Receipt to keep for whatever you run

| Field | Value |
| --- | --- |
| Source URL | |
| Exact tag (never `latest`) | |
| Local model ID / digest | |
| Size on disk | |
| Quantization | |
| Base model and licence | |
| Who made the edit, and what they say they changed | |
| Runtime and version | |
| Pull date | |
| Reason for choosing it | |

## Vetting checklist (planned, C07)

Treat a third-party weight edit like an unreviewed pull request with a shell.

- [ ] Provenance: who published it, how long they've published, whether the edit method is documented.
- [ ] Integrity: digest recorded at pull and compared before each session (AU-03 compares the served name; compare the digest by hand until automated).
- [ ] Licence: the base model's licence permits your use.
- [ ] Capability is not honesty: a good score says nothing about hidden behaviour.
- [ ] Limit what it can do: no tools by default, sandboxed tools when needed, no egress (C10, C14). This matters more than any behavioural check, because a trigger you don't know about won't show up in a test you wrote.
- [ ] Differential checks: keep a small fixed prompt set and its outputs; rerun after any change and look for unexplained differences (P10).
