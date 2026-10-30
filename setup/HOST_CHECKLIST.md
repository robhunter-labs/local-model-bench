# Host checklist

Paraphrased from the setup guide I followed in October, with placeholders for anything specific to my machines. Tick boxes are for your copy.

**Host used:** one macOS laptop with a dedicated, non-admin inference account. One model, about 39 GB on disk.

## 1. Account and disk
- [ ] Dedicated non-admin account for inference (`INFERENCE_USER`).
- [ ] Full-disk encryption on; normal OS updates.
- [ ] Check free disk before pulling a large model. Don't delete other data to make room.

## 2. Remote access
- [ ] Remote Login (SSH) on for that account only.
- [ ] Key from the client installed; key login works; *then* password login off.
- [ ] Record the host key fingerprint on the client at first connection, and compare it every time it's asked.
- [ ] Firewall allows SSH; nothing else inbound. The model port is never opened to the network.
- [ ] Planned: a dedicated tunnel key restricted to one forward (see `controls/BASELINE.md`, C16).

## 3. Runtime
- [ ] Install Ollama from its official instructions. Leave auto-start off until manual setup works.
- [ ] Set the environment in `controls/BASELINE.md` (loopback, cloud off, one model, one request, 8K context to start). Restart the app.
- [ ] Run `python3 bench/run_bench.py --i-own-this-host --category network-exposure --model PIN` on the host. NE-01 and NE-02 must pass.

## 4. Model
- [ ] Pull exactly one pinned tag. Never `latest`.
- [ ] Record tag, local ID/digest, size, runtime version, date and source URL in your own receipt (see `WEIGHTS.md`).
- [ ] One bring-up request on the host. Watch memory pressure and swap.

## 5. Client
- [ ] Open the tunnel from the client (see `NETWORK.md`), repeat the request, close the tunnel, confirm access ends (NE-03).
- [ ] Point the harness at the tunnel's local port (see `HARNESS_PI.md`).

## After any reboot, logout or update
- [ ] Re-run NE-01, NE-02 and AU-03 before a client uses the host.
