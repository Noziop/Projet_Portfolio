#!/bin/bash

# Function to install dependencies
install_deps() {
    poetry config virtualenvs.create false
    poetry lock --no-update
    poetry install --no-interaction --no-ansi
}

# Initial install
install_deps

# Start Celery worker
exec celery -A app.core.celery worker --loglevel=info
