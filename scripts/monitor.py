"""Separate host collector and read-only web processes."""
import argparse
import json
import os
import time
from pathlib import Path

from filelock import FileLock, Timeout

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['collect', 'web'])
    parser.add_argument('--once', action='store_true')
    parser.add_argument('--port', type=int, default=8787)
    args = parser.parse_args()
    runtime = ROOT / '.runtime'
    runtime.mkdir(exist_ok=True)
    snapshot = runtime / 'monitoring.json'
    if args.mode == 'web':
        from codex_harness.adapters.monitoring_web import serve
        serve(snapshot, args.port)
        return
    from codex_harness.adapters.monitoring import collect
    from codex_harness.bootstrap import build_executor, redis_url
    os.chdir(ROOT)
    try:
        with FileLock(str(runtime / 'monitor-collector.lock'), timeout=0):
            executor = build_executor()
            while True:
                result = collect(executor.service, executor.artifacts, str(ROOT), redis_url())
                temp = snapshot.with_suffix('.tmp')
                temp.write_text(json.dumps(result, ensure_ascii=False), 'utf-8')
                os.replace(temp, snapshot)
                if args.once:
                    return
                time.sleep(5)
    except Timeout:
        return


if __name__ == '__main__':
    main()
