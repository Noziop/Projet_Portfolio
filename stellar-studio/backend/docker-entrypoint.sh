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

# Installation des dépendances simplifiée
install_deps() {
    poetry config virtualenvs.create false
    # Ignorer les warnings de poetry en redirigeant stderr
    poetry install --no-interaction --no-ansi 2>/dev/null
}

# Installation initiale
install_deps || true

# Démarrer le watcher en arrière-plan et sauvegarder son PID
watchmedo shell-command \
    --patterns="pyproject.toml" \
    --recursive \
    --command='poetry install --no-interaction --no-ansi 2>/dev/null' &
BACKGROUND_PID=$!

# Démarrer l'application
poetry run alembic upgrade head
poetry run python -c "from app.db.init_db import init_db; from app.db.session import SessionLocal; init_db(SessionLocal())"
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
