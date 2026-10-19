# ==============================================================================
# Multi-Stage Production Dockerfile: MedOps-Sentinel v1.0
# Autonomous Clinical AI Drift Firewall & SRE Engine
# ==============================================================================

# Stage 1: Build & Dependency Wheel Cache
FROM python:3.11-slim AS builder

WORKDIR /build

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip wheel --no-cache-dir --no-deps --wheel-dir /build/wheels -r requirements.txt


# Stage 2: Minimal Distroless / Hardened Runtime
FROM python:3.11-slim AS runtime

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MEDOPS_ENV=production \
    PORT=8000

# Install curl for Docker/Kubernetes healthcheck probe
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install pre-built wheels from builder stage
COPY --from=builder /build/wheels /wheels
COPY requirements.txt .
RUN pip install --no-cache /wheels/* && rm -rf /wheels

# Copy application source & static cockpit
COPY app.py server.py ./
COPY static/ ./static/
COPY tests/ ./tests/

# Create non-root dedicated service user for clinical security compliance
RUN groupadd -r medops && useradd -r -g medops -s /bin/false medops && \
    chown -R medops:medops /app

USER medops

# Expose SRE telemetry & cockpit port
EXPOSE 8000

# Container Healthcheck (Kubernetes readiness & liveness compatible)
HEALTHCHECK --interval=15s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Start Uvicorn ASGI Server
CMD ["python", "-m", "uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2", "--log-level", "info"]
