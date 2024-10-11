from django_filters import rest_framework as filters
from .models import Product

class ProductFilter(filters.FilterSet):
    price_min = filters.NumberFilter(field_name="price", lookup_expr='gte')
    price_max = filters.NumberFilter(field_name="price", lookup_expr='lte')
    qnt_min = filters.NumberFilter(field_name="qnt", lookup_expr='gte')
    qnt_max = filters.NumberFilter(field_name="qnt", lookup_expr='lte')

    class Meta:
        model = Product
        fields = ['category', 'is_active', 'price_min', 'price_max', 'qnt_min', 'qnt_max']
