# Data flow

```text
  [operator] ──prompt, fixtures──▶ [harness on client] ──HTTP over SSH tunnel──▶ [model server on host]
      ▲                                │   ▲                                         │
      │ decides every effect           │   │ model output (untrusted)                 │ reads
      │                                ▼   │                                         ▼
      └──── results, logs ◀──── [guard] ──▶ [inert tools / fixtures] ──results──▶  [model files, logs]
                                   │  (TB3)            (TB4: results are data)        (TB5, TB6)
                                   ▼
                           [sandbox, no egress]  (planned)
```

| Flow | Crosses | Carries | Protection today |
| --- | --- | --- | --- |
| Client harness → model server | TB1, TB2 | prompts, fixtures | SSH tunnel to a loopback listener |
| Model server → client | TB2, TB3 | completions, proposed tool calls | none beyond the tunnel; the guard is built, not yet in path |
| Tool → model context | TB4 | tool results | fencing built, not yet in path |
| Weights → runtime | TB5 | behaviour nobody disclosed | tag and digest recorded; no vetting yet |
| Host → disk | TB6 | prompt history, server logs | account separation; not audited |
| Host → network | TB6 | anything a compromised host chooses | macOS firewall (unverified) |

## Assets

| Asset | Where | Why someone would want it |
| --- | --- | --- |
| Prompts and logs | host and client | they record what I was working on |
| The tunnel key and the host's trust in it | client, host | a path from the host back to the client |
| Model files | host | tampering target (swap the weights, keep the name) |
| Network seat | host | a foothold on the local network |
| Client secrets | client | the real prize; the harness must never hand them to a tool |
