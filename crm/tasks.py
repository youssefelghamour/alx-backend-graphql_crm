from celery import shared_task
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
from datetime import datetime


@shared_task
def generate_crm_report():
    transport = RequestsHTTPTransport(
        url='http://localhost:8000/graphql',
        verify=True,
        retries=3,
    )

    client = Client(transport=transport, fetch_schema_from_transport=True)

    query = gql("""
        query {
            customers { id }
            orders { id, totalAmount }
        }
    """)

    result = client.execute(query)

    customer_count = len(result['customers'])
    order_count = len(result['orders'])
    total_revenue = sum(float(order['totalAmount']) for order in result['orders'])

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    log_line = (
        f"[{now}] Report: {customer_count} customers, {order_count} orders, ${total_revenue:.2f} revenue\n"
    )

    with open('crm/tmp/crm_report.log', 'a') as log_file:
        log_file.write(log_line)
    
    print("CRM report generated and logged.")