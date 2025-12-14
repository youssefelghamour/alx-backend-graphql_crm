import django_filters
from .models import Customer, Product, Order


class CustomerFilter(django_filters.FilterSet):
    """Customer filter"""
    name = django_filters.CharFilter(field_name="name", lookup_expr="icontains")
    email = django_filters.CharFilter(field_name="email", lookup_expr="icontains")
    createdAtGte = django_filters.DateFilter(field_name="created_at", lookup_expr="gte")
    createdAtLte = django_filters.DateFilter(field_name="created_at", lookup_expr="lte")
    phone_starts_with = django_filters.CharFilter(
        field_name="phone",
        lookup_expr="startswith"
    )

    class Meta:
        model = Customer
        fields = ["name", "email", "createdAtGte", "createdAtLte", "phone_starts_with"]


class ProductFilter(django_filters.FilterSet):
    """Product filter"""
    name = django_filters.CharFilter(field_name="name", lookup_expr="icontains")
    price = django_filters.RangeFilter(field_name="price")
    stock = django_filters.RangeFilter(field_name="stock")
    # When set to true this filters only products that are on low stock using the method
    lowStock = django_filters.BooleanFilter(method="filter_low_stock")

    def filter_low_stock(self, queryset, name, value):
        """Custom filter for products on low stock (<10)"""
        if value:
            return queryset.filter(stock__lt=10)
        return queryset

    class Meta:
        model = Product
        fields = ["name", "price", "stock", "lowStock"]


class OrderFilter(django_filters.FilterSet):
    """Order filter"""
    totalAmountGte = django_filters.NumberFilter(field_name="total_amount", lookup_expr="gte")
    totalAmountLte = django_filters.NumberFilter(field_name="total_amount", lookup_expr="lte")
    orderDateAfter = django_filters.DateFilter(field_name="order_date", lookup_expr="gte")
    orderDateBefore = django_filters.DateFilter(field_name="order_date", lookup_expr="lte")
    customerName = django_filters.CharFilter(field_name="customer__name", lookup_expr="icontains")
    productName = django_filters.CharFilter(field_name="products__name", lookup_expr="icontains")
    product_id = django_filters.NumberFilter(field_name="products__id", lookup_expr="exact")

    class Meta:
        model = Order
        fields = [
            "totalAmountGte",
            "totalAmountLte",
            "orderDateAfter",
            "orderDateBefore",
            "customerName",
            "productName",
            "product_id",
        ]