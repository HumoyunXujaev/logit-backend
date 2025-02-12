import django_filters
from django.db.models import Q
from .models import Cargo

class CargoFilter(django_filters.FilterSet):
    min_weight = django_filters.NumberFilter(
        field_name='weight',
        lookup_expr='gte'
    )
    max_weight = django_filters.NumberFilter(
        field_name='weight',
        lookup_expr='lte'
    )
    min_volume = django_filters.NumberFilter(
        field_name='volume',
        lookup_expr='gte'
    )
    max_volume = django_filters.NumberFilter(
        field_name='volume',
        lookup_expr='lte'
    )
    loading_date_from = django_filters.DateFilter(
        field_name='loading_date',
        lookup_expr='gte'
    )
    loading_date_to = django_filters.DateFilter(
        field_name='loading_date',
        lookup_expr='lte'
    )
    price_from = django_filters.NumberFilter(
        field_name='price',
        lookup_expr='gte'
    )
    price_to = django_filters.NumberFilter(
        field_name='price',
        lookup_expr='lte'
    )
    
    location = django_filters.CharFilter(method='filter_location')
    radius = django_filters.NumberFilter(method='filter_radius')
    
    class Meta:
        model = Cargo
        fields = {
            'status': ['exact'],
            'vehicle_type': ['exact', 'in'],
            'loading_type': ['exact', 'in'],
            'payment_method': ['exact'],
            'is_constant': ['exact'],
            'is_ready': ['exact'],
        }
    
    def filter_location(self, queryset, name, value):
        """
        Filter by loading or unloading point, supporting partial matches
        """
        if not value:
            return queryset
            
        return queryset.filter(
            Q(loading_point__icontains=value) |
            Q(unloading_point__icontains=value)
        )
    
    def filter_radius(self, queryset, name, value):
        """
        Filter by radius around loading or unloading point
        Placeholder - implement actual geo radius search
        """
        # TODO: Implement actual geo radius search using PostGIS
        # For now, return unfiltered queryset
        return queryset