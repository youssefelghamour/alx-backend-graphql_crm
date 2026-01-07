from crm.models import Customer
from django.utils.timezone import now
from datetime import timedelta

one_year_ago = now() - timedelta(days=365)
deleted_count = 0

for customer in Customer.objects.all():
    orders = customer.orders.all()

    # If all orders are older than a year, delete this customer
    if orders.exists() and all(order.order_date < one_year_ago for order in orders):
        print(f"Deleting customer {customer.id} - {customer.name}")
        customer.delete()
        deleted_count += 1
    
# Log the number of deleted customers to a /tmp/customer_cleanup_log.txt with a timestamp
with open('crm/cron_jobs/tmp/customer_cleanup_log.txt', 'a') as log_file:
    log_file.write(f"{now()}: Deleted {deleted_count} customers\n")  