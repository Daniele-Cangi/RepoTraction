"""Opt-in boundary probes: execute only fixed probe code, never acquired code."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from missing_link.wasi_runner import WasiRunner

BOUNDARY = '''import json, os, sys
assert sys.platform == "wasi", sys.platform
assert not any("KEY" in key or "TOKEN" in key or key.startswith("GH_") for key in os.environ)
denied = []
for path in ("/etc/passwd", "C:/Users/dacan/.codex", "/sandbox/../.env", "/sandbox/work/../../../../.env"):
    try:
        open(path).read()
    except OSError:
        denied.append(path)
    else:
        raise AssertionError("Host filesystem readable")
try:
    import subprocess
    subprocess.run(["cmd.exe", "/c", "echo", "unsafe"], check=True)
except (ImportError, OSError, NotImplementedError):
    pass
else:
    raise AssertionError("Native subprocess available")
try:
    import socket
    socket.create_connection(("127.0.0.1", 8765), timeout=1)
except (ImportError, OSError, AttributeError, NotImplementedError):
    pass
else:
    raise AssertionError("Network available")
print(json.dumps({"platform": sys.platform, "environment_keys": sorted(os.environ), "host_paths_denied": denied,
    "native_process_denied": True, "network_denied": True}))
'''


def verify():
    runner = WasiRunner()
    results = {"boundary": runner.run({"probe.py": BOUNDARY}, "probe.py"),
        "fuel": runner.run({"probe.py": "while True: pass\n"}, "probe.py"),
        "memory": runner.run({"probe.py": "x = bytearray(300 * 1024 * 1024)\n"}, "probe.py"),
        "output": runner.run({"probe.py": "print('x' * 100000)\n"}, "probe.py")}
    results["passed"] = (results["boundary"]["status"] == "exited_successfully"
        and "fuel consumed" in results["fuel"].get("stderr", "")
        and "MemoryError" in results["memory"].get("stderr", "") and results["output"]["status"] == "output_limit")
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    results = verify()
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps({key: value if key == "passed" else {"status": value["status"],
        "stdout": value.get("stdout", "")[:1000], "stderr": value.get("stderr", "")[:1000]}
        for key, value in results.items()}, indent=2))
    raise SystemExit(0 if results["passed"] else 1)
