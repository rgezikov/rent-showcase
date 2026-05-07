# ============================================================
# Stage 1: Build Tailwind CSS (production only)
# ============================================================
FROM node:20-alpine AS css-builder
WORKDIR /app
COPY package.json ./
RUN npm install
COPY tailwind.config.js ./
COPY static/src/ ./static/src/
COPY templates/ ./templates/
RUN npm run build

# ============================================================
# Stage 2: Python base
# ============================================================
FROM python:3.12-slim AS base

COPY --from=ghcr.io/astral-sh/uv:0.5 /uv /uvx /usr/local/bin/

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml uv.lock* ./
RUN uv sync --no-install-project

COPY . .
RUN uv sync

# ============================================================
# Stage 3: Development target
# ============================================================
FROM base AS dev
RUN uv run playwright install --with-deps chromium
CMD ["uv", "run", "python", "manage.py", "runserver", "0.0.0.0:8000"]

# ============================================================
# Stage 4: Production target
# ============================================================
FROM base AS prod

COPY --from=css-builder /app/static/css/output.css ./static/css/output.css

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
CMD ["uv", "run", "gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
