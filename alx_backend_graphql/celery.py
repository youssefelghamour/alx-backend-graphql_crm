import os
from celery import Celery

os.environ.setdefault(
    'DJANGO_SETTINGS_MODULE',
    'alx_backend_graphql.settings'
)

app = Celery('alx_backend_graphql')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()