#!/bin/bash

# Définir une variable pour tracker les processus en arrière-plan
BACKGROUND_PID=""

cleanup() {
    # Si on a un PID en arrière-plan, le tuer proprement
    if [ ! -z "$BACKGROUND_PID" ]; then
        kill $BACKGROUND_PID 2>/dev/null
    fi
}

# Mettre en place le trap pour le nettoyage
trap cleanup EXIT

# Vérification de santé
health_check() {
    if ! poetry check; then
        echo "Poetry check failed, running lock..."
        poetry lock --no-update
        if ! poetry check; then
            echo "Poetry check still failed after lock"
            return 1
        fi
    fi
    return 0
}

install_deps() {
    if ! health_check; then
        echo "Health check failed"
        exit 1
    fi
    poetry config virtualenvs.create false
    poetry install --no-interaction --no-ansi
}

# Installation initiale
install_deps

# Démarrer le watcher en arrière-plan et sauvegarder son PID
watchmedo shell-command \
    --patterns="pyproject.toml" \
    --recursive \
    --command='poetry lock --no-update && poetry install' &
BACKGROUND_PID=$!

# Démarrer l'application
poetry run alembic upgrade head
poetry run python -c "from app.db.init_db import init_db; from app.db.session import SessionLocal; init_db(SessionLocal())"
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

