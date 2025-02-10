# app/core/celery.py
from celery import Celery
from kombu import Exchange, Queue

celery_app = Celery(
    "stellar_studio",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/0",
    include=[
        'app.services.task.service',
        'app.tasks.download',
        'app.tasks.processing'
    ]
)

# Définition des queues
default_exchange = Exchange('default', type='direct')
download_exchange = Exchange('download', type='direct')
processing_exchange = Exchange('processing', type='direct')

celery_app.conf.update(
    broker_connection_retry_on_startup=True,
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Europe/Paris',
    enable_utc=True,
    worker_send_task_events=True,
    task_send_sent_event=True,
    worker_hostname_format='{name}.{queue}.{timestamp}',
    worker_proc_name='%(queue)s-%(n)d',
    task_default_queue='download_queue',
    task_queues=(
        Queue('download_queue', exchange=download_exchange, routing_key='download'),
        Queue('processing_queue', exchange=processing_exchange, routing_key='processing'),
    ),
    task_routes={
        'app.tasks.download.*': {'queue': 'download_queue'},
        'app.tasks.processing.*': {'queue': 'processing_queue'},
    },
    # Pas de timeout
    task_time_limit=None,
    task_soft_time_limit=None,
    broker_transport_options={'visibility_timeout': 43200},  # 12 heures
    result_expires=None,  # Résultats jamais expirés
)
