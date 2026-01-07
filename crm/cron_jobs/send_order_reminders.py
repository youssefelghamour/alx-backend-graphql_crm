"""Python script that uses a GraphQL query to find pending orders (order_date within the last week)
    and logs reminders, scheduled to run daily using a cron job
"""
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
from datetime import datetime, timedelta


transport = RequestsHTTPTransport(
    url="http://localhost:8000/graphql",
    verify=True,
    retries=3,
)

client = Client(transport=transport)


week_ago = (datetime.now() - timedelta(days=7)).date().isoformat()

query = gql("""
    query ($weekAgo: Date!) {
        allOrders(orderDateAfter: $weekAgo) {
            edges {
                node {
                    id
                    customer {
                        email
                    }
                }
            }
        }
    }
""")

result = client.execute(query, variable_values={"weekAgo": week_ago})

for edge in result["allOrders"]["edges"]:
    order = edge["node"]
    customer_email = order["customer"]["email"]
    order_id = order["id"]

    with open("order_reminders_log.txt", "a") as log_file:
        timestamp = datetime.now()
        log_file.write(f"[{timestamp}] - Order ID: {order['id']}, Customer Email: {customer_email}\n")

print("Order reminders processed!")