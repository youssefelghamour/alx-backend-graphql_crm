# ALX Backend GraphQL CRM

GraphQL-based CRM backend built with Django, supporting customers, products, and orders with filtering, sorting, and robust validation.

## Features

- CRUD for Customers, Products, and Orders via GraphQL mutations  
- Bulk customer creation with partial success handling  
- Nested order creation with product associations  
- Validation and user-friendly error messages  
- GraphQL queries with filtering, sorting, and pagination  

## Tech Stack

- Django  
- graphene-django  
- django-filter  
- PostgreSQL/MySQL (optional)  
- GraphiQL / Insomnia for testing  

## GraphQL Endpoint

`http://localhost:8000/graphql`  

### Example Queries

- **Customers**
  - Simple List Query:

```graphql
query {
    customers {
        id
        name
        email
        phone
        createdAt
    }
}
```

  - Relay-Style Query:

```graphql
query {
    allCustomers {
        edges {
            node {
                id
                name
                email
                phone
                orders {
                    edges {
                        node {
                            totalAmount
                            orderDate
                            products {
                                id
                                name
                                price
                                stock
                            }
                        }
                    }
                }
                createdAt
            }
        }
    }
}
```

- **Products**
  - Simple List Query:

```graphql
query {
    products {
        id
        name
        price
        stock
    }
}
```

  - Relay-Style Query:

```graphql
query {
    allProducts {
        edges {
            node {
                id
                name
                price
                stock
            }
        }
    }
}
```

- **Orders**
  - Simple List Query:

```graphql
query {
    orders {
        id
        customer {
            id
            name
            email
            phone
        }
        products {
            id
            name
            price
            stock
        }
        totalAmount
        orderDate
    }
}
```

  - Relay-Style Query:

```graphql
query {
    allOrders {
        edges {
            node {
                id
                customer {
                    id
                    name
                    email
                    phone
                }
                products {
                    id
                    name
                    price
                    stock
                }
                totalAmount
                orderDate
            }
        }
    }
}
```

### Example Mutations

- **Create Customer** – create a single customer with name, email, and phone.

```graphql
mutation {
    createCustomer(input: {
        name: "Youssef",
        email: "youssef@example.com",
        phone: "+1234567890"
    }) {
        customer {
            id
            name
            email
            phone
        }
        message
    }
}
```

- **Bulk Create Customers** – create multiple customers in one request

```graphql
mutation {
    bulkCreateCustomers(input: [
        { name: "customer1", email: "customer1@example.com", phone: "123-456-7890" },
        { name: "customer2", email: "customer2@example.com" }
    ]) {
        customers {
            id
            name
            email
        }
        errors
    }
}
```

- **Create Product** – create a product with name, price, and stock

```graphql
mutation {
    createProduct(input: {
        name: "Laptop",
        price: 999.99,
        stock: 10
    }) {
        product {
            id
            name
            price
            stock
        }
    }
}
```

- **Create Order** – create an order for a customer and associate product

```graphql
mutation {
    createOrder(input: {
        customerId: "1",
        productIds: ["1", "2"]
    }) {
        order {
            id
            customer {
                name
            }
            products {
                name
                price
            }
            totalAmount
            orderDate
        }
    }
}
```


### Example Queries (Filters)
- **Customers** – filter by name, creation date, email, or phone pattern.

```graphql
query {
    allCustomers(name: "Youssef", createdAtGte: "2025-01-01") {
        edges {
            node {
                id
                name
                email
                createdAt
            }
        }
    }
}
```

- **Products** – filter by name, price range, stock, or low stock.

```graphql
query {
    allProducts(price: "100-1000", lowStock: false, orderBy: "-stock") {
        edges {
            node {
                id
                name
                price
                stock
            }
        }
    }
}
```

- **Orders** – filter by customer name, product name, total amount, or order date.

```graphql
query {
    allOrders(
        customerName: "Youssef",
        productName: "Laptop",
        totalAmountGte: 500
    ) {
        edges {
            node {
                id
                customer {
                    name
                }
                products {
                    name
                }
                totalAmount
                orderDate
            }
        }
    }
}
```
