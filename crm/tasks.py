from celery import shared_task

@shared_task
def generate_crm_report():
    print("Generating CRM report...")