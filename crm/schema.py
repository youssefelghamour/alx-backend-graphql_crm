import graphene
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from crm.models import Product, Customer, Order
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
from .filters import CustomerFilter, ProductFilter, OrderFilter
import re


PHONE_REGEX = re.compile(r"^(\+\d{10,15}|\d{3}-\d{3}-\d{4})$")


# ────────────── TYPES ──────────────

class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer
        interfaces = (graphene.relay.Node,)
        filterset_class = CustomerFilter
        fields = ("id", "name", "email", "phone", "orders", "created_at")

    def resolve_orders(self, info):
        return self.orders.all()

class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        interfaces = (graphene.relay.Node,)
        filterset_class = ProductFilter
        fields = ("id", "name", "price", "stock")

class OrderType(DjangoObjectType):
    products = graphene.List(ProductType)  # override connection with plain list

    class Meta:
        model = Order
        interfaces = (graphene.relay.Node,)
        filterset_class = OrderFilter
        fields = ("id", "customer", "products", "total_amount", "order_date")
    
    def resolve_products(self, info):
        return list(self.products.all())



# ────────────── INPUTS ──────────────

class CreateCustomerInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    email = graphene.String(required=True)
    phone = graphene.String()

class BulkCreateCustomersInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    email = graphene.String(required=True)
    phone = graphene.String()

class CreateProductInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    price = graphene.Float(required=True) 
    stock = graphene.Int()

class CreateOrderInput(graphene.InputObjectType):
    customer_id = graphene.ID(required=True)
    product_ids = graphene.List(graphene.ID, required=True)
    order_date = graphene.DateTime()



# ────────────── MUTATIONS ──────────────

class CreateCustomer(graphene.Mutation):
    """ Creates a single customer
        Input Fields:
            name: required string
            email: required unique string
            phone: optional string (+1234567890 or 123-456-7890)
        Logic:
            Checks email uniqueness
            Validates phone format
            Creates customer in database
        Return:
            customer object
            success message
    """
    class Arguments:
        input = CreateCustomerInput(required=True)

    customer = graphene.Field(CustomerType)
    message = graphene.String()

    def mutate(self, info, input):
        # Ensure email is unique
        if Customer.objects.filter(email=input.email).exists():
            raise ValidationError("Email already exists")
        
        # Validate phone format
        if input.phone and not PHONE_REGEX.match(input.phone):
            raise ValidationError("Invalid phone format. Use +1234567890 or 123-456-7890")
        
        customer = Customer.objects.create(
            name=input.name, email=input.email, phone=input.phone
        )
        return CreateCustomer(customer=customer, message="Customer created")


class BulkCreateCustomers(graphene.Mutation):
    """ Creates multiple customers in bulk
        Input Fields:
            List of customers, each with:
                name: required string
                email: required unique string
                phone: optional string (+1234567890 or 123-456-7890)
        Logic:
            Validates each customer
            Creates valid entries
            Collects errors for invalid entries
        Return:
            list of successfully created customers
            list of errors
    """
    class Arguments:
        input = graphene.List(BulkCreateCustomersInput, required=True)

    customers = graphene.List(CustomerType)
    errors = graphene.List(graphene.String)

    def mutate(self, info, input):
        created = []
        errors = []
        for c in input:
            # Ensure email is unique
            if Customer.objects.filter(email=c.email).exists():
                errors.append(f"Email {c.email} already exists")
                continue
            
            # Validate phone format
            if c.phone and not PHONE_REGEX.match(c.phone):
                errors.append(f"Invalid phone format for {c.email}")
                continue

            customer = Customer.objects.create(
                name=c.name, email=c.email, phone=c.phone
            )
            created.append(customer)
        return BulkCreateCustomers(customers=created, errors=errors)


class CreateProduct(graphene.Mutation):
    """ Creates a single product
        Input Fields:
            name: required string
            price: required positive float
            stock: optional int (default 0, non-negative)
        Logic:
            Validates price and stock
            Creates product in database
        Return:
            product object
    """
    class Arguments:
        input = CreateProductInput(required=True)

    product = graphene.Field(ProductType)

    def mutate(self, info, input):
        # Convert price from float to Decimal
        price = Decimal(str(input.price))

        # Ensure price is positive
        if input.price <= 0:
            raise ValidationError("Price must be positive")
        
        # Ensure stock is not negative
        if input.stock is not None and input.stock < 0:
            raise ValidationError("Stock cannot be negative")
        stock_value = input.stock if input.stock is not None else 0

        product = Product.objects.create(
            name=input.name, price=price, stock=stock_value
        )
        return CreateProduct(product=product)


class CreateOrder(graphene.Mutation):
    """
        Input Fields:
            customer_id: required existing ID
            product_ids: required list of existing IDs
            order_date: optional datetime (defaults to now)
        Logic:
            Validates customer and product IDs
            Ensures at least one product
            Calculates total_amount
            Creates order and associates products
        Return:
            order object with nested customer and products
    """
    class Arguments:
        input = CreateOrderInput(required=True)

    order = graphene.Field(OrderType)

    def mutate(self, info, input):
        # Ensure customer ID is valid
        try:
            customer = Customer.objects.get(id=input.customer_id)
        except Customer.DoesNotExist:
            raise ValidationError("Invalid customer ID")

        if not input.product_ids:
            raise ValidationError("At least one product must be selected")

        # Ensure all product IDs are valid
        products = Product.objects.filter(id__in=input.product_ids)
        if not products.exists() or len(products) != len(input.product_ids):
            # If one is invalid don't proceed
            raise ValidationError("Invalid product IDs")

        # Calculate the total amount for this order
        total_amount = sum([Decimal(str(p.price)) for p in products])
        order_date = input.order_date if input.order_date else timezone.now()

        order = Order(customer=customer, order_date=order_date)
        order.save()
        order.products.add(*products)
        order.total_amount = sum(p.price for p in products)
        order.save()

        return CreateOrder(order=order)


class UpdateLowStockProducts(graphene.Mutation):
    """
        Mutation to update stock levels of products that are low in stock (stock < 10)
        Logic:
            Find products with stock below 10
            Restock: increase their stock by 10
        Return:
            list of updated products
            and a success message
    """
    products = graphene.List(ProductType)
    message = graphene.String()

    def mutate(self, info):
        low_stock_products = Product.objects.filter(stock__lt=10)

        # Keep track of the low stock products that will be updated
        ids = [product.id for product in low_stock_products]

        for product in low_stock_products:
            product.stock += 10
            product.save()
        
        # Query again the products to return the updated instances
        updated_products = Product.objects.filter(id__in=ids)

        return UpdateLowStockProducts(
            products=list(updated_products),
            message="Low stock products have been restocked by 10 units each."
        )


# ────────────── QUERY ──────────────

class Query(graphene.ObjectType):
    hello = graphene.String(default_value="Hello, GraphQL!")
    customers = graphene.List(CustomerType)
    products = graphene.List(ProductType)
    orders = graphene.List(OrderType)

    def resolve_customers(root, info):
        return Customer.objects.all()

    def resolve_products(root, info):
        return Product.objects.all()

    def resolve_orders(root, info):
        return Order.objects.all()

    # FILTERS

    # Customers query with filters and ordering
    all_customers = DjangoFilterConnectionField(
        CustomerType,
        orderBy=graphene.List(of_type=graphene.String)  # Argument to sort customers (by name, email, created_at in asc/desc order)
    )

    def resolve_allCustomers(self, info, orderBy=None, **kwargs):
        qs = Customer.objects.all()  # Start with all customers
        if kwargs:  # Apply filters from CustomerFilter (name, email, createdAtGte/Lte, phone_starts_with)
            qs = CustomerFilter(kwargs, queryset=qs).qs
        if orderBy:  # Apply ordering if provided
            qs = qs.order_by(*orderBy)
        return qs

    # Products query with filters and ordering
    all_products = DjangoFilterConnectionField(
        ProductType,
        orderBy=graphene.List(of_type=graphene.String)  # Argument to sort products (by name, price, stock in asc/desc order)
    )

    def resolve_allProducts(self, info, orderBy=None, **kwargs):
        qs = Product.objects.all()  # Start with all products
        if kwargs:  # Apply filters from ProductFilter (name, price, stock, lowStock)
            qs = ProductFilter(kwargs, queryset=qs).qs
        if orderBy:  # Apply ordering if provided
            qs = qs.order_by(*orderBy)
        return qs

    # Orders query with filters and ordering
    all_orders = DjangoFilterConnectionField(
        OrderType,
        orderBy=graphene.List(of_type=graphene.String)  # Argument to sort orders (by order_date, total_amount, customer__name in asc/desc order)
    )

    def resolve_allOrders(self, info, orderBy=None, **kwargs):
        qs = Order.objects.all()  # Start with all orders
        if kwargs:  # Apply filters from OrderFilter (customerName, productName, totalAmountGte/Lte, orderDateAfter/Before, product_id)
            qs = OrderFilter(kwargs, queryset=qs).qs
        if orderBy:  # Apply ordering if provided
            qs = qs.order_by(*orderBy)
        return qs

# ────────────── MUTATION ──────────────

class Mutation(graphene.ObjectType):
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()
    update_low_stock_products = UpdateLowStockProducts.Field()