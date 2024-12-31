FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    pkg-config \
    default-libmysqlclient-dev \
    build-essential \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app/downloads && \
    chown -R appuser:appuser /app && \
    chmod 777 /app/downloads

# Install poetry and watchdog
RUN pip install poetry watchdog

# Configure poetry to not create virtualenv
RUN poetry config virtualenvs.create false

# Copy dependency files
COPY pyproject.toml ./

# Install dependencies as root
RUN poetry install --no-interaction --no-ansi

# Copy entrypoint script
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh && \
    chown -R appuser:appuser /usr/local/bin/docker-entrypoint.sh

ENV PYTHONPATH=/app
ENV HOME=/home/appuser

USER appuser

EXPOSE 8000
ENTRYPOINT ["docker-entrypoint.sh"]
