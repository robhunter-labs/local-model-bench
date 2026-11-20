# Timing run: October 21, 2026 · MacBook Pro · Qwen 3.6 27B

Companion to [*Where the Time Goes on a Local Model*](https://robhunterworks.com/writing/where-the-time-goes-on-a-local-model/). Figure 2 there is drawn from this file's CSV.

The run used a MacBook Pro with an M4 Max and 48 GB of unified memory, with Ollama serving the model on the same machine. The call records cover one stock Qwen 3.6 27B run through Ollama 0.32.14. The run used 4,096 tokens of context, a 192-token output cap and temperature 0.2. The recorded setup identifies Q4_K_M weights. A separate pre-run Ollama model inventory reported 17,420,432,739 bytes (17.4 GB) for the matching model digest. The timing CSV does not measure installed bytes or free space.

Eight short synthetic tasks in two versions and two repetitions produced 32 calls. Inputs ran from 165 to 254 tokens and output from 12 to 61.

| Measure | Result |
| --- | --- |
| First and second call, model-side | 12.79 s and 4.35 s |
| Model load, first call | 10.18 s |
| Model load, later calls | 0.18 s median |
| Load plus prompt evaluation | 11.43 s first, 1.40 s median later |
| Output generation | 20.8 tokens/s median (19.4 to 22.0) |
| Prompt evaluation | 162 tokens/s median (132 to 177) across 30 calls |
| Total per call | 4.42 s median (1.95 to 12.79) |
| Sum of reported per-call duration | 135.5 s across 32 calls |

The load-plus-prompt figure estimates server-side work before generation. The record has no streaming measurement of time to first token. The sum of reported per-call durations is a time budget and excludes any unrecorded client overhead.

Calls 30 and 32 show much faster apparent prompt throughput. They were excluded from the prompt-rate row only. Cache reuse is plausible. The timing CSV has no explicit cache count or trace for those calls.

[Figure 2](../../figures/FIGURE_2_WHERE_THE_SECONDS_WENT.svg) plots the three Ollama phases for every call, without the small residual between the plotted phases and the reported total. The [CSV](per_call.csv) retains each row's timing and token metadata. `reported_at_utc` preserves the original recorded timestamp without assigning it to the start of the call. The CSV contains no prompt or reply text.

The run did not vary settings, measure power or heat, record peak memory, or score the quality of the answers. A November storage relocation is separate evidence and adds no timings to this table.
