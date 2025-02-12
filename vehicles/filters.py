import django_filters
from .models import Vehicle

class VehicleFilter(django_filters.FilterSet):
    min_capacity = django_filters.NumberFilter(
        field_name='capacity',
        lookup_expr='gte'
    )
    max_capacity = django_filters.NumberFilter(
        field_name='capacity',
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
    
    location = django_filters.CharFilter(method='filter_location')
    has_valid_documents = django_filters.BooleanFilter(
        method='filter_valid_documents'
    )
    
    class Meta:
        model = Vehicle
        fields = {
            'body_type': ['exact', 'in'],
            'loading_type': ['exact', 'in'],
            'is_active': ['exact'],
            'is_verified': ['exact'],
            'adr': ['exact'],
            'dozvol': ['exact'],
            'tir': ['exact'],
            'registration_country': ['exact'],
        }
    
    def filter_valid_documents(self, queryset, name, value):
        """
        Filter vehicles by presence of verified documents
        """
        if value is True:
            return queryset.filter(
                documents__verified=True
            ).distinct()
        return queryset.exclude(
            documents__verified=True
        ).distinct()
    
    def filter_location(self, queryset, name, value):
        """
        Filter vehicles by current location
        based on latest availability record
        """
        if value:
            return queryset.filter(
                availability__location__icontains=value
            ).distinct()
        return queryset