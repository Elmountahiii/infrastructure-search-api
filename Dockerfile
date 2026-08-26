FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.11.27 /uv /uvx /bin/

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-dev --no-install-project

COPY app ./app
COPY scripts ./scripts
COPY samples ./samples
COPY docker-entrypoint.sh ./docker-entrypoint.sh

RUN addgroup --system app \
    && adduser --system --ingroup app app \
    && mkdir -p /app/data \
    && chown app:app /app/data \
    && chmod +x /app/docker-entrypoint.sh

USER app

EXPOSE 8000

CMD ["/app/docker-entrypoint.sh"]
