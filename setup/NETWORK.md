# Network and tunnel

The model server has no real authentication, so the network design *is* the access control.

- The server listens on loopback only on the inference host (NE-01, NE-02).
- Clients reach it through a restricted tunnel to the inference port only: one forward, no shell, no agent forwarding (C16, `planned`). The tunnel layout and key restrictions are kept out of this public copy.
- The harness points at the tunnel's local end as an OpenAI-compatible base URL (`http://127.0.0.1:LOCAL_PORT/v1`). Use the same port in the harness config.

Rules:
- Never bind the server to `0.0.0.0` or any network address "for convenience."
- The API key field some clients demand is a placeholder. It is not a lock (AU-01, AU-02).
- Anything the tunnel reaches, anyone holding the tunnel reaches, including model-management paths unless you filter them. A small path-filtering proxy on the host closes that (C19); AU-04 checks it.
- Closing the tunnel must end access (NE-03).

**Observed in October:** the tunnel connected and a terminal client on the main machine got answers through it. Most testing then ran on the host itself. The full client path through a harness hasn't been tested.
