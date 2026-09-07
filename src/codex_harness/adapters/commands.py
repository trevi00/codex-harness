from __future__ import annotations

import os
import signal
import subprocess


def run_process(argv: list[str], cwd: str | None = None, timeout: int = 120,
                input_text: str | None = None) -> subprocess.CompletedProcess:
    """Terminate our own process tree on timeout, including cmd -> node on Windows."""
    kwargs = {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == "nt" else {"start_new_session": True}
    process = subprocess.Popen(argv, cwd=cwd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace", **kwargs)
    try:
        stdout, stderr = process.communicate(input_text, timeout=timeout)
    except (subprocess.TimeoutExpired, KeyboardInterrupt):
        if os.name == "nt":
            subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                           capture_output=True, timeout=20)
        else:
            os.killpg(process.pid, signal.SIGKILL)
        process.communicate()
        raise
    return subprocess.CompletedProcess(argv, process.returncode, stdout, stderr)
