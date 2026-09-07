"""Create a local-only database credential; never print it or overwrite an existing one."""
import secrets
from pathlib import Path

root = Path(__file__).resolve().parents[1]
env = root / ".env"
if not env.exists():
    password = secrets.token_hex(24)
    env.write_text(
        f"POSTGRES_PASSWORD={password}\n"
        f"HARNESS_DATABASE_URL=postgresql://harness:{password}@127.0.0.1:55432/harness\n",
        encoding="utf-8",
    )
    print("Created .env (local credential; gitignored)")
else:
    print("Existing .env retained")
