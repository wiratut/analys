FROM node:20-bookworm-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    REFLEX_USE_GRANIAN=false \
    REFLEX_CHECK_LATEST_VERSION=false \
    PATH="/opt/venv/bin:${PATH}"

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    fonts-noto-core \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    python3 \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN python3 -m venv /opt/venv \
    && pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["/bin/sh", "-c", "reflex run --env prod --single-port --frontend-port ${PORT:-10000} --backend-port ${PORT:-10000} --backend-host 0.0.0.0"]
