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


def update_low_stock():
    """Executes the UpdateLowStockProducts mutation to restock low inventory products (stock < 10)
        And logs updated product names and new stock levels to /tmp/low_stock_updates_log.txt
    """
    mutation = gql("""
        mutation {
            updateLowStockProducts {
                products {
                    name
                    stock
                }
            }
        }
    """)

    try:
        response = client.execute(mutation)
        updated_products = response['updateLowStockProducts']['products']
        
        log_path = "/root/alx-backend-graphql_crm/crm/cron_jobs/tmp/low_stock_updates_log.txt"
        
        with open(log_path, "a") as log_file:
            timestamp = datetime.now().strftime("%d/%m/%Y-%H:%M:%S")
            for product in updated_products:
                log_file.write(f"[{timestamp}] Product: {product['name']}, New Stock: {product['stock']}\n")
    except Exception as e:
        print(f"Failed to update low stock products: {e}")