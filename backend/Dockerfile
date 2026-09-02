# Stage 1: Build stage
FROM python:3.12-slim AS base
WORKDIR /app

# Install uv binary
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Create a clean virtual environment
RUN python -m venv /venv
ENV PATH="/venv/bin:$PATH"

# Install Python packages into /venv with uv cache AND compile bytecode
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=requirements.txt,target=requirements.txt \
    uv pip install --compile-bytecode -r requirements.txt


# Stage 2: Final runtime stage
FROM python:3.12-slim AS final
WORKDIR /app

# Install system libraries via apt-get
RUN apt-get update && apt-get install -y --no-install-recommends \
    poppler-utils \
    tesseract-ocr \
    tesseract-ocr-eng \
    libmagic1 \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN addgroup --system appgroup && adduser --system --group appuser

# Copy the populated virtual environment from build stage
COPY --from=base /venv /venv
ENV PATH="/venv/bin:$PATH"

# Copy application source code
COPY --chown=appuser:appgroup src/ ./src

ENV PYTHONPATH=/app/src
ENV FLASK_APP=src/app.py

USER appuser
EXPOSE 5000

CMD ["flask", "run", "--host=0.0.0.0"]