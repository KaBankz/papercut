# ============================================================================
# Stage 1: Builder - Install dependencies
# ============================================================================
FROM python:3.14-slim AS builder

RUN pip install uv --no-cache

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-dev --no-install-project --no-cache

# ============================================================================
# Stage 2: Runtime - Production image with USB support
# ============================================================================
FROM python:3.14-slim

# Build arguments for dynamic labels set by Makefile
ARG TITLE
ARG DESCRIPTION
ARG VERSION
ARG AUTHORS
ARG LICENSE
ARG BUILD_DATE
ARG VCS_REF
ARG VCS_URL

# OCI Standard Labels
# See: https://github.com/opencontainers/image-spec/blob/main/annotations.md
LABEL org.opencontainers.image.title="${TITLE}" \
      org.opencontainers.image.description="${DESCRIPTION}" \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.created="${BUILD_DATE}" \
      org.opencontainers.image.authors="${AUTHORS}" \
      org.opencontainers.image.url="${VCS_URL}" \
      org.opencontainers.image.documentation="${VCS_URL}#readme" \
      org.opencontainers.image.source="${VCS_URL}" \
      org.opencontainers.image.revision="${VCS_REF}" \
      org.opencontainers.image.licenses="${LICENSE}"

# Install USB libraries required for python-escpos
RUN apt update && \
    apt install -y --no-install-recommends \
        libusb-1.0-0 \
        wget && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv

COPY src/ ./src/
COPY config.py main.py papercut.toml ./

# Create /config directory for user's mounted config
RUN mkdir -p /config

# Add venv to PATH and src to PYTHONPATH
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH="/app/src" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 -O /dev/null http://127.0.0.1:8000/ || exit 1

# Run the application with optimized settings
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
