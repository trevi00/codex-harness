"""Initialize Git-owned project stack configuration; import legacy YAML explicitly."""
import argparse
import json
from pathlib import Path

from codex_harness.adapters.project_skills import initialize


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', type=Path)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--config', type=Path)
    source.add_argument('--from-claude', action='store_true')
    args = parser.parse_args()
    path = args.root / '.claude/tech-stack.yaml' if args.from_claude else args.config
    print(json.dumps(initialize(args.root, path.read_text('utf-8-sig')), ensure_ascii=False))


if __name__ == '__main__':
    main()
