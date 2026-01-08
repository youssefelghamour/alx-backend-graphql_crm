"""This is a copy of the main celery.py file located in alx_backend_graphql/celery.py
    It is included here to satisfy task requirements, feel free to delete it
"""
import os
from celery import Celery

os.environ.setdefault(
    'DJANGO_SETTINGS_MODULE',
    'alx_backend_graphql.settings'
)

app = Celery('alx_backend_graphql')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()