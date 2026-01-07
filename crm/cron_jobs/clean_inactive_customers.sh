#!/bin/bash
# A script that uses manage.py shell to execute a Python command that deletes customers with no orders since a year ago

# Move from the directory of this script to the project root where manage.py is located
cd "$(dirname "$0")/../.."

# Execute the Python script using Django's manage.py shell to delete customers
# with no orders in the last 365 days, print progress, and count deletions
python manage.py shell -c "exec(open('crm/cron_jobs/clean_inactive_customers.py').read())"