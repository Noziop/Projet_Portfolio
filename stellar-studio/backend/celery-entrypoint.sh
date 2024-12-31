#!/bin/bash

# Start Celery worker
exec celery -A app.core.celery worker --loglevel=info
