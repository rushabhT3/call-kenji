# The voice server. The web page ships separately as static assets.
FROM ghcr.io/astral-sh/uv:0.12.22 AS uv

FROM python:3.12.15-slim-trixie AS build
COPY --from=uv /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=never
WORKDIR /app
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev --no-install-project
COPY src ./src
RUN uv sync --frozen --no-dev

FROM python:3.12.15-slim-trixie
RUN useradd --create-home --uid 10001 kenji && mkdir /data && chown kenji /data
WORKDIR /app
COPY --from=build --chown=kenji /app/.venv ./.venv
COPY --from=build --chown=kenji /app/src ./src
COPY --chown=kenji content ./content
ENV PATH="/app/.venv/bin:$PATH" \
    HOST=0.0.0.0 \
    PORT=8080 \
    DATA_DIR=/data \
    PYTHONUNBUFFERED=1
USER kenji
EXPOSE 8080
CMD ["kenji-server"]
