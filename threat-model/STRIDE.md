# Threat model: STRIDE table

Scope is the setup in [`../SPEC.md`](../SPEC.md): one inference host, one client, an SSH tunnel, a harness. Boundaries TB1–TB6 are defined there; the data flow is in [`DATA_FLOW.md`](DATA_FLOW.md).

The table is generated from [`../pentest/traceability.json`](../pentest/traceability.json). Edit the JSON, then run `python3 tools/render_docs.py`.

<!-- BEGIN GENERATED -->
| ID | STRIDE | Boundary | Threat | Controls | Bench cases | Pen-test methods |
| --- | --- | --- | --- | --- | --- | --- |
| T01 | Spoofing | TB1 | **Anyone on the network calls the model API.** The inference server has no real authentication. If it listens beyond loopback, any device on the network can use it, read model behaviour or abuse admin endpoints. | C01, C02, C16 | NE-01, AU-01, AU-02 | P01, P02 |
| T02 | Spoofing | TB2 | **Tunnel set up to the wrong host.** An unverified host key lets a look-alike host receive the client's prompts and present itself as the model. | C03 | NE-03 | P03 |
| T03 | Tampering | TB5 | **Backdoored or poisoned weights.** A third-party weight edit may carry trigger behaviour that only appears with tools attached. Benchmarks measure capability, not honesty. | C06, C07, C10, C14 | AU-03, HP-05 | P10, P09 |
| T04 | Tampering | TB4 | **Instructions planted in tool output steer the model.** Text returned by a tool or document is read by the model and may contain instructions. | C12, C10, C15 | PI-01, PI-02, PI-03, HP-04 | P07 |
| T05 | Repudiation | TB3 | **Nobody can reconstruct what the model was asked or did.** Without request and response records, a misbehaving session can't be investigated or a result reproduced. | C13, C17 | LG-01, LG-02 | P12 |
| T06 | Information disclosure | TB6 | **Prompts and logs read from the host's disk.** The host keeps model files and logs, which means a record of what was sent to the model. | C04, C17 | DL-02, LG-02 | P05 |
| T07 | Information disclosure | TB6 | **Secrets reachable from the host.** Keys, environment files, cloud credentials or mounted source on the host are exactly what a malicious model or tool would look for. | C08, C04 | DL-03 | P05 |
| T08 | Information disclosure | TB3 | **Data leaves through a tool call or rendered link.** A model that can trigger a fetch, a request or a rendered image link can move data out. | C14, C10, C12 | PI-01, PI-03, DL-01 | P09 |
| T09 | Denial of service | TB1 | **Host made unusable by huge or parallel requests.** Very large contexts and concurrent requests exhaust memory or tie the host up for many minutes. | C09 | RL-01, RL-02, RL-03 | P11 |
| T10 | Elevation of privilege | TB3 | **Proposed tool calls run without enforcement.** Observed: the model made two tool calls at once despite a one-at-a-time rule. A prompt can ask; only a harness can enforce. | C10, C11, C15 | HP-01, HP-02, HP-03, HP-05 | P08 |
| T11 | Elevation of privilege | TB2 | **A compromised host reaches the client.** The host is trusted over SSH and sits on the local network. Agent forwarding, broad keys or reused credentials turn it into a foothold. | C16, C03, C02 | NE-03 | P04, P13 |
| T12 | Tampering | TB5 | **Silent model or runtime drift.** A re-pull or update changes the bytes under a result without anyone noticing. | C06, C18 | AU-03 | P10 |
| T13 | Information disclosure | TB1 | **Cloud features send prompts off the box.** Optional cloud features in the runtime could route prompts to a hosted service. | C05 | NE-02 | P05 |
| T14 | Elevation of privilege | TB3 | **Wrong-but-valid output gets acted on.** Observed: valid JSON with wrong arithmetic, and a missed stolen-credential signal. Formatting is not truth. | C15, C11 | RE-01, RE-02, RE-03 | P07 |
| T15 | Tampering | TB1 | **Admin endpoints reachable through the tunnel.** Anyone holding the tunnel can reach model-management endpoints (pull, create, delete), not just chat. | C19, C16 | AU-04 | P06 |
<!-- END GENERATED -->

## How I'd use this

Start with the threats that are cheap to check and catastrophic to miss: T01 (the listener), T07 (secrets on the host) and T11 (the host as a foothold). Then T10 and T04, which are where the October runs actually failed. T03 has no complete answer; the realistic aim is to shrink what a misbehaving model could *do*, since I can't fully verify what it *is*.

This is a working model for one small setup. It isn't a template for an enterprise deployment, which would need its own threat model with its own owners.
