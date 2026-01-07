from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
from datetime import datetime


transport = RequestsHTTPTransport(
    url="http://localhost:8000/graphql",
    verify=True,
    retries=3,
)

client = Client(transport=transport)

query = gql("""
    query { hello }
""")

def log_crm_heartbeat():
    """django-crontab job that logs a heartbeat message every 5 minutes to confirm the CRM application’s health"""
    try:
        client.execute(query)
        status = "CRM is alive"
    except Exception:
        status = "CRM is down"

    log_path = "/root/alx-backend-graphql_crm/crm/cron_jobs/tmp/crm_heartbeat_log.txt"
    
    with open(log_path, "a") as log_file:
        timestamp = datetime.now().strftime("%d/%m/%Y-%H:%M:%S")
        log_file.write(f"{timestamp} {status}\n")
