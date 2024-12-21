#!/bin/bash

trap 'kill $(jobs -p)' EXIT

# Et une vérification de santé
health_check() {
    poetry check
    if [ $? -ne 0 ]; then
        echo "Poetry check failed"
        exit 1
    fi
}

install_deps() {
    health_check
    poetry config virtualenvs.create false
    poetry lock --no-update
    poetry install --no-interaction --no-ansi
}

# Initial install
install_deps

# Start dependency watcher in background
watchmedo shell-command \
    --patterns="pyproject.toml" \
    --recursive \
    --command='poetry lock --no-update && poetry install' &

# Start the application
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
