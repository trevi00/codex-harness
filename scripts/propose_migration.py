"""Explicit operator action: creates a proposal and fresh reviews, never approvals."""
import argparse
import json
from pathlib import Path

from codex_harness.adapters.evaluator_migration import propose_migration
from codex_harness.adapters.git import GitWorkspace
from codex_harness.application.releases import Releases
from codex_harness.bootstrap import build
from codex_harness.domain.model import canonical


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--candidate-json', required=True)
    parser.add_argument('--repository', required=True)
    parser.add_argument('--workspaces', required=True)
    args = parser.parse_args()
    candidate = json.loads(Path(args.candidate_json).read_text())
    service = build()
    record = propose_migration(Releases(service.store, service.org),
                               GitWorkspace(args.repository, args.workspaces), candidate)
    print(canonical({'release_id': record['id'], 'policy_hash': record['policy_hash'],
                     'policy': record['policy'], 'status': record['status']}))


if __name__ == '__main__':
    main()
