FROM node:22-bookworm-slim AS codex
RUN npm install -g @openai/codex@0.153.4
FROM python:3.13-slim-bookworm
RUN apt-get update && apt-get install -y --no-install-recommends git ca-certificates && rm -rf /var/lib/apt/lists/*
COPY --from=codex /usr/local/bin/node /usr/local/bin/node
COPY --from=codex /usr/local/lib/node_modules /usr/local/lib/node_modules
RUN ln -s /usr/local/lib/node_modules/@openai/codex/bin/codex.js /usr/local/bin/codex
WORKDIR /app
COPY pyproject.toml uv.lock ./
COPY src ./src
RUN pip install --no-cache-dir uv==0.12.2 && uv sync --frozen --no-dev
ENV PATH="/app/.venv/bin:$PATH"
ENTRYPOINT ["harness"]
