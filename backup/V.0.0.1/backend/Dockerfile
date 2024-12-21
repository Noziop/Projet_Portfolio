# Stage de build
FROM python:3.9-slim AS builder

# Installation de Poetry
RUN pip install poetry

WORKDIR /app
COPY pyproject.toml .

# Configuration de Poetry pour ne pas créer de virtualenv
RUN poetry config virtualenvs.create false

# Installation des dépendances
RUN poetry install --no-root

# Stage final
FROM python:3.9-slim

WORKDIR /app
COPY --from=builder /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY . .

EXPOSE 80
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]
