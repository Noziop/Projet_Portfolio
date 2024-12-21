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


# Install poetry and watchdog
RUN pip install poetry watchdog

# Copy dependency files and entrypoint script
COPY pyproject.toml ./
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

ENV PYTHONPATH=/app

EXPOSE 8000
ENTRYPOINT ["docker-entrypoint.sh"]
