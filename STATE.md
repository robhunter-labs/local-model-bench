# Current state and future state

As of late October 2026. Every "future" row is **not done**.

## Current state

| Area | State |
| --- | --- |
| Host | One laptop set up per [`setup/HOST_CHECKLIST.md`](setup/HOST_CHECKLIST.md). Loopback listener and cloud-off observed once at setup. |
| Model | One pinned refusal-reduced derivative. Tag and digest recorded privately. No vetting beyond that. |
| Network | SSH tunnel connected once; a terminal client got answers through it. Most testing ran on the host itself. |
| Harness | October runs used a private hand-built harness with no tools attached. Pi not used yet. |
| Observations | Capacity, reliability and knowledge pilots summarized in [`results/pilot-transcribed/`](results/pilot-transcribed/SUMMARY.md). |
| This repo | Method bank (26 cases, 8 categories), runner, reference guard, scorers, traceability (15 threats, 19 controls, 13 pen-test methods), docs generated from data. Tests and dry run pass. **Not yet run against the real host or model.** |

## Future state, in the order I'd do it

| # | Step | Closes | Status |
| --- | --- | --- | --- |
| 1 | Run host checks on the real host (NE-01, NE-02, DL-02, DL-03) and fix what they find | T01, T06, T07, T13 | planned |
| 2 | Restrict the tunnel key to one forward; agent forwarding off (C16) | T11, T15 | planned |
| 3 | Run the endpoint and model cases through the tunnel (AU-*, PI-*, DL-01, RL-*, RE-*) | T04, T08, T09, T14 | planned |
| 4 | Small path-filtering proxy so only chat and model-list are reachable (C19) | T15 | planned |
| 5 | Wire Pi to the tunnel; put the guard's rules in a Pi extension; run tools in a container with no network | T10, T08 | planned |
| 6 | Rerun the October failures *through* the harness: HP-05, RE-01, RE-02, with model compliance and guard enforcement scored separately | T10, T14 | planned |
| 7 | Weights vetting per [`setup/WEIGHTS.md`](setup/WEIGHTS.md) and a fixed differential prompt set | T03, T12 | planned |
| 8 | Run the pen-test map ([`pentest/TEST_MAP.md`](pentest/TEST_MAP.md)) and disposition every finding | all | planned |
| 9 | Fill in the standards mapping honestly, including what isn't covered | — | planned |
| 10 | Write up what held and what didn't | — | planned |

The bench is "done enough for advisory use" when the success bar in [`SPEC.md`](SPEC.md) is met. It isn't yet.

## Not planned

Fine-tuning or training ([`setup/TRAINING.md`](setup/TRAINING.md)); multi-user serving; real targets or real data; unattended tool use.
