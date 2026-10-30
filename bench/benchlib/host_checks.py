"""Checks meant to run ON the inference host. Read-only: they inspect local state and
try to connect to the host's own addresses. They never read file contents for the
secrets inventory, only names, sizes and permissions.
"""
from __future__ import annotations

import os
import socket
import stat
import subprocess
from pathlib import Path


def _local_addresses() -> list[str]:
    addrs = set()
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            addrs.add(info[4][0])
    except socket.gaierror:
        pass
    # Best-effort discovery of the primary outbound interface without sending traffic.
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("192.0.2.1", 9))  # TEST-NET-1, never routed; connect() on UDP sends nothing
        addrs.add(s.getsockname()[0])
        s.close()
    except OSError:
        pass
    return sorted(a for a in addrs if not a.startswith("127."))


def _can_connect(host: str, port: int, timeout: float = 1.5) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def listener_loopback_only(port: int = 11434) -> dict:
    on_loopback = _can_connect("127.0.0.1", port)
    exposed = {a: _can_connect(a, port) for a in _local_addresses()}
    bad = [a for a, ok in exposed.items() if ok]
    if not on_loopback:
        return {"result": "inconclusive", "detail": f"nothing answering on 127.0.0.1:{port}; is the server running?", "observations": exposed}
    return {"result": "fail" if bad else "pass",
            "detail": f"reachable on non-loopback addresses: {bad}" if bad else "answers on loopback only",
            "observations": {"loopback": on_loopback, "non_loopback": exposed}}


def _launchctl_getenv(name: str):
    try:
        out = subprocess.run(["launchctl", "getenv", name], capture_output=True, text=True, timeout=5)
        return out.stdout.strip() or None
    except (FileNotFoundError, subprocess.SubprocessError):
        return None


def cloud_disabled(var: str = "OLLAMA_NO_CLOUD") -> dict:
    value = os.environ.get(var) or _launchctl_getenv(var)
    if value is None:
        return {"result": "fail", "detail": f"{var} not set in the environment or launchd", "observations": {var: None}}
    return {"result": "pass" if value in ("1", "true", "TRUE") else "fail", "detail": f"{var}={value}", "observations": {var: value}}


def storage_permissions(path: str = "~/.ollama") -> dict:
    root = Path(path).expanduser()
    if not root.exists():
        return {"result": "inconclusive", "detail": f"{root.name} not found", "observations": {}}
    loose = []
    count = 0
    for p in root.rglob("*"):
        if p.is_symlink():
            continue
        count += 1
        mode = p.stat().st_mode
        if mode & (stat.S_IROTH | stat.S_IWOTH):
            loose.append(str(p.relative_to(root)))
    return {"result": "fail" if loose else "pass",
            "detail": f"{len(loose)} of {count} entries readable or writable by other users" if loose else f"{count} entries, none world-accessible",
            "observations": {"world_accessible": loose[:50]}}


SECRET_NAME_PATTERNS = (".env", "id_rsa", "id_ed25519", "id_ecdsa", "credentials", ".netrc", ".npmrc", ".pypirc")
SECRET_DIRS = (".aws", ".config/gcloud", ".azure", ".kube", ".docker", ".gnupg")


def secrets_inventory(home: str = "~", max_depth: int = 3) -> dict:
    """Names only. Never opens a file. Anything found should be moved off the inference host."""
    root = Path(home).expanduser()
    found = [d for d in SECRET_DIRS if (root / d).exists()]
    for dirpath, dirnames, filenames in os.walk(root):
        depth = Path(dirpath).relative_to(root).parts
        dirnames[:] = [d for d in dirnames if d not in (".ollama", "Library", ".Trash")]
        if len(depth) >= max_depth:
            dirnames[:] = []
        for f in filenames:
            if f.endswith(".pub") or f == "known_hosts" or f == "authorized_keys":
                continue
            if any(f == pat or f.startswith(pat) for pat in SECRET_NAME_PATTERNS):
                found.append(str(Path(dirpath, f).relative_to(root)))
    return {"result": "fail" if found else "pass",
            "detail": f"{len(found)} likely secret locations on the host" if found else "no likely secret locations found by name",
            "observations": {"names": sorted(set(found))[:100]}}


CHECKS = {
    "listener_loopback_only": listener_loopback_only,
    "cloud_disabled": cloud_disabled,
    "storage_permissions": storage_permissions,
    "secrets_inventory": secrets_inventory,
}
