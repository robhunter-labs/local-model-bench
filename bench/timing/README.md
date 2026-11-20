# Time a local model

This folder holds the small Python tool behind [*Where the Time Goes on a Local Model*](https://robhunterworks.com/writing/where-the-time-goes-on-a-local-model/), for timing an Ollama model on your own machine.

## Start with the recorded run

Open the [results summary](../../results/2026-10-21-timing/SUMMARY.md) or [Figure 2](../../figures/FIGURE_2_WHERE_THE_SECONDS_WENT.svg). The first call spent 10.18 seconds loading the model. Later calls spent a median 0.18 seconds on that step. Across all 32 calls, answer generation had a median rate of 20.8 tokens per second.

You can recalculate the table with Python 3.9+ and the standard library. This step needs no Ollama server or model download.

```sh
python3 bench/timing/summarize_timing.py results/2026-10-21-timing/per_call.csv --exclude-prompt-rate-orders 30 32
```

The two exclusions apply only to the prompt-rate row. Both calls remain in the chart and in every other calculation. The log does not confirm a cache hit.

## Time your own machine

Run the commands from the repository root. Start Ollama locally and select an already installed model from `ollama list`. Use the supplied [short sample prompts](sample_prompts.jsonl) for a quick run, or substitute a JSONL file with a short, non-sensitive `id` and a `prompt` per line.

```sh
python3 bench/timing/run_timing.py --i-own-this-host --model "<installed model tag>" \
    --prompts bench/timing/sample_prompts.jsonl \
    --repeats 2 --num-ctx 4096 --cold-start --out runs/example.jsonl
python3 bench/timing/summarize_timing.py runs/example.jsonl
```

`--i-own-this-host` confirms you own the machine or are authorized to test it, the same acknowledgement the rest of the bench asks for. The sample prompts exercise the tool, not the publication's original tasks. The runner connects over loopback, reports the model digest and run settings, and writes timing metadata without prompt or answer text. Use a fresh output filename for each run. An interrupted run can be summarized and is labeled partial.

- `--cold-start` asks Ollama to unload the model before each context block. This does not clear the operating system's file cache.
- `--num-ctx 4096 8192` compares two requested context sizes in separate summary blocks. Use deliberately longer prompts if your question is about long inputs.
- `--models-dir` tells the runner which local volume to check for free space. An unavailable path is reported as unavailable. Placement reads Ollama's model memory report, which is different from peak system memory use.
- The requests are non-streaming. Load plus prompt-evaluation time is a server-side estimate of preparation time, and the runner separately records elapsed client time until the full response.

To regenerate the timing chart from the published rows, run:

```sh
python3 figures/fig2_timing.py --out runs/where-the-seconds-went.svg
```

Create the destination directory first, or choose an existing directory.

## What this can answer

The recorded result describes short requests to one model on one machine. Try a cold request and a warm request before judging how the same setup feels. Use separate exercises for quality, long-context behavior, power or peak memory, and evidence that actions stayed within their boundary.

The earlier security pilot and the clean-room bench in this repository have their own evidence and quickstarts; see the [repository README](../../README.md).
