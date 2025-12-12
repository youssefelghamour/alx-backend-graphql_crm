import os
import django
from decimal import Decimal
from django.utils import timezone


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "alx_backend_graphql.settings")
django.setup()


from crm.models import Customer, Product, Order


# ───── Customers ─────
customers_data = [
    {"name": "Customer 1", "email": "customer1@example.com", "phone": "+10000000001"},
    {"name": "Customer 2", "email": "customer2@example.com", "phone": "100-000-0002"},
    {"name": "Customer 3", "email": "customer3@example.com", "phone": None},
    {"name": "Customer 4", "email": "customer4@example.com", "phone": "+10000000004"},
]

customers = []
for c in customers_data:
    customer = Customer.objects.create(**c)
    customers.append(customer)


# ───── Products ─────
products_data = [
    {"name": "Laptop", "price": Decimal("999.99"), "stock": 10},
    {"name": "Mouse", "price": Decimal("49.99"), "stock": 50},
    {"name": "Keyboard", "price": Decimal("79.99"), "stock": 30},
    {"name": "Monitor", "price": Decimal("199.99"), "stock": 20},
]

products = []
for p in products_data:
    product = Product.objects.create(**p)
    products.append(product)


# ───── Orders ─────
orders_data = [
    {"customer": customers[0], "product_indices": [0, 2]},     # Customer 1 buys Laptop + Keyboard
    {"customer": customers[1], "product_indices": [1]},        # Customer 2 buys Mouse
    {"customer": customers[2], "product_indices": [2, 3]},     # Customer 3 buys Keyboard + Monitor
    {"customer": customers[3], "product_indices": [0, 1, 3]},  # Customer 4 buys Laptop + Mouse + Monitor
]

for o in orders_data:
    order = Order.objects.create(customer=o["customer"], order_date=timezone.now())
    order.products.add(*[products[i] for i in o["product_indices"]])
    order.total_amount = sum(products[i].price for i in o["product_indices"])
    order.save()

print("Seeding completed successfully")