"""Initialize Git-owned project stack configuration; import legacy YAML explicitly."""
import argparse
import json
from pathlib import Path

from codex_harness.adapters.project_skills import initialize
from codex_harness.domain.model import ContractError


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', type=Path)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--config', type=Path)
    source.add_argument('--from-claude', action='store_true')
    args = parser.parse_args()
    path = args.root / '.claude/tech-stack.yaml' if args.from_claude else args.config
    try:
        result = initialize(args.root, path.read_text('utf-8-sig'), legacy=args.from_claude)
    except (OSError, ContractError) as exc:
        parser.exit(2, json.dumps({'error': type(exc).__name__, 'message': str(exc)}) + '\n')
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
