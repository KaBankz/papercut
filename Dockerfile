# ============================================================================
# Stage 1: Builder - Install dependencies
# ============================================================================
FROM python:3.14-alpine AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-dev --no-install-project --no-cache

# ============================================================================
# Stage 2: Runtime - Ultra-minimal production image
# ============================================================================
FROM python:3.14-alpine

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
      org.opencontainers.image.documentation="${VCS_URL}/blob/-/README.md" \
      org.opencontainers.image.source="${VCS_URL}" \
      org.opencontainers.image.revision="${VCS_REF}" \
      org.opencontainers.image.licenses="${LICENSE}"

# Install only runtime dependencies (if any are needed by your deps)
# Most Python apps on Alpine need libgcc, libstdc++
RUN apk add --no-cache libgcc libstdc++ && \
    rm -rf /var/cache/apk/*

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv

COPY *.py ./

# Create non-root user for security
RUN addgroup -g 1000 appuser && \
    adduser -D -u 1000 -G appuser appuser && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Add venv to PATH
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Expose port
EXPOSE 8000

# Health check (using minimal wget)
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8000/ || exit 1

# Run the application with optimized settings
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
