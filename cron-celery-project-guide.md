# Crons: Scheduling and Automating Tasks

In this Django project I automated CRM tasks using system cron jobs, django-crontab, and Celery with Beat.  
It improves the CRM by cleaning inactive customers, sending order reminders, updating low stock, logging heartbeat messages, and generating weekly reports.

I used three types of task scheduling in this project:

1. **System Cron Jobs (Ubuntu)**: ran shell scripts and Python scripts directly via cron
2. **Django Cron Jobs (`django-crontab`)**: scheduled tasks within Django using crontab entries defined in `settings.py`
3. **Asynchronous Tasks with Celery & Redis**:
    - Used `Celery` workers to run tasks asynchronously.
    - And `Celery Beat` schedules periodic tasks.
    - Used `Redis` as the message broker.

## Overview

We enhanced the CRM with the following:

- **Customer Cleanup:** Deletes customers with no orders in the last year.
- **Order Reminders:** Queries GraphQL for orders from the last 7 days and logs reminders.
- **Heartbeat Logger:** Logs "CRM is alive" every 5 minutes to ensure the app is responsive.
- **Low Stock Updates:** Updates products with stock < 10 via a GraphQL mutation.
- **Weekly CRM Reports:** Uses Celery with Beat to generate weekly reports (customers, orders, revenue) asynchronously.
- **Improvements:** Added logging, fixed type errors, and ensured tasks run reliably without interfering with the main app.




## 1. System Cron Jobs (Ubuntu)

These tasks are executed on Ubuntu not on windows as it doesn't support cron.

### Setup Cron on Ubuntu

```bash
# 1. Install cron
sudo apt install cron -y

# 2. Start the cron service
service cron start

# 3. Check cron status, make sure it's running
service cron status

# 4. List current cron jobs: this will print out the content if the cron file exists
crontab -l

# 5. Edit cron jobs: this will open the cron file, edit it by adding entries at the end of the file, save & close
crontab -e
```

---

### Customer Cleanup

- **File:** `crm/cron_jobs/clean_inactive_customers.sh`  
- **Python Logic:** `crm/cron_jobs/clean_inactive_customers.py`  
- **Log:** `crm/cron_jobs/tmp/customer_cleanup_log.txt`

**Purpose:** Deletes customers with no orders in the past year and logs the count.

**Cron Entry:**  
```bash
0 2 * * 0 /root/alx-backend-graphql_crm/crm/cron_jobs/clean_inactive_customers.sh
```

---

### Order Reminders

- **File:** `crm/cron_jobs/send_order_reminders.py`  
- **Log:** `crm/cron_jobs/tmp/order_reminders_log.txt`

**Purpose:** Queries the GraphQL API for orders in the past week and logs reminders for each order.

**Cron Entry:**  
```bash
0 8 * * * /root/alx-backend-graphql_crm/crm/cron_jobs/send_order_reminders.py
```







## 2. Django Cron Jobs (django-crontab)

These tasks run inside Django without needing Redis.
- This requires that `django-crontab` is installed (included in requirements.txt), and then added to INSTALLED_APPS in settings.py.
- Functions executed by django-crontab exists in `crm/cron.py`.
- The cron jobs are included in `settings.py`:
```bash
CRONJOBS = [
    ('*/5 * * * *', 'crm.cron.log_crm_heartbeat'),
    ('0 */12 * * *', 'crm.cron.update_low_stock'),
]
```

### Heartbeat Logger

**File:** `crm/cron.py`  
**Log:** `/tmp/crm_heartbeat_log.txt`

**Purpose:** Logs "CRM is alive" or "CRM is down" every 5 minutes after querying GraphQL to ensure API is responsive.

**Setup:**

```bash
# Install cron jobs
python manage.py crontab add

# Show active jobs
python manage.py crontab show

# Remove cron jobs
python manage.py crontab remove
```

---

### Low Stock Updates

**File:** `crm/cron.py`  
**Log:** `/tmp/low_stock_updates_log.txt`  

**Purpose:** Runs a GraphQL mutation to increment stock of products with stock < 10, every 12 hours.

**Cron Schedule:**  
```bash
0 */12 * * * crm.cron.update_low_stock
```






## 3. Celery Tasks with Beat

This handles asynchronous, scheduled tasks that can scale.

### CRM Reports

**File:** `crm/tasks.py`  
**Log:** `/tmp/crm_report_log.txt`

**Purpose:** Generates weekly reports (total customers, orders, revenue) and logs them.

**Architecture:**

1. **Celery Beat:** Schedules tasks.
2. **Redis Broker:** Acts as a message queue between Beat and Worker.
3. **Celery Worker:** Picks up tasks from Redis and executes them.
4. **Logging:** Results stored in `/tmp/crm_report_log.txt`.

![celery-architecture](./assets/celery-architecture-diagram.png)

Basically, Celery's job is to execute tasks asynchronously in the background. These are tasks that take time, like sending emails, or tasks that don’t need to return a result. Instead of making the user wait for them, we run them in the background.  

We use a scheduler like **Celery Beat** to automate and schedule these tasks, similar to cron jobs. Beat sends the task (written as a function in `tasks.py`) to **Redis**, which acts as a message broker, then to Celery that receives it, and then spawns a worker to execute the task in the background.

On Beat terminal it looks like this:
```bash
[2026-01-08 21:39:09,698: INFO/MainProcess] Scheduler: Sending due task generate-crm-report (crm.tasks.generate_crm_report)
```

On Celery terminal it looks like this:
```bash
[2026-01-08 21:39:09,711: INFO/MainProcess] Task crm.tasks.generate_crm_report[f044b8c9-0722-44da-8cf4-b2c925a0729e] received
[2026-01-08 21:39:11,916: WARNING/MainProcess] CRM report generated and logged.
[2026-01-08 21:39:11,924: INFO/MainProcess] Task crm.tasks.generate_crm_report[f044b8c9-0722-44da-8cf4-b2c925a0729e] succeeded in 2.219000000040978s: None
```


**Setup:**

Start Redis with Docker

```bash
docker compose up -d redis
```

In the first terminal, run the Django app so so celery can send request to the API

```bash
python manage.py runserver
```

In a second terminal, start Celery worker

```bash
celery -A alx_backend_graphql worker -l info --pool=solo
```

> On Windows, Celery requires `--pool=solo` so that it runs workers in a single process instead of spawning a new process for each task received from the Beat scheduler through Redis.

In a third terminal, start Celery Beat scheduler
```bash
celery -A alx_backend_graphql beat -l info
```

**Notes:**  
- `celery.py` includes the Celery setup, and `__init__.py` ensures the app can import it correctly. 
- **Celery settings using Redis** are included at the end of `settings.py`:  
```bash
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_TIMEZONE = 'UTC'
```
- Beat scheduled tasks are also defined at the end of `settings.py`:
```bash
CELERY_BEAT_SCHEDULE = {
    'generate-crm-report': {
        'task': 'crm.tasks.generate_crm_report',
        'schedule': crontab(day_of_week='mon', hour=6, minute=0),
    },
}
```
- Celery must be restarted if task code was modified or schedule changes.