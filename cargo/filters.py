import django_filters
from django.db.models import Q
from .models import Cargo
from core.models import Location
from math import radians, cos, sin, asin, sqrt

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
    
    # Фильтры для Location
    loading_location = django_filters.ModelChoiceFilter(
        queryset=Location.objects.filter(level=3),
        field_name='loading_location'
    )
    unloading_location = django_filters.ModelChoiceFilter(
        queryset=Location.objects.filter(level=3),
        field_name='unloading_location'
    )
    loading_country = django_filters.ModelChoiceFilter(
        queryset=Location.objects.filter(level=1),
        method='filter_loading_country'
    )
    unloading_country = django_filters.ModelChoiceFilter(
        queryset=Location.objects.filter(level=1),
        method='filter_unloading_country'
    )
    loading_state = django_filters.ModelChoiceFilter(
        queryset=Location.objects.filter(level=2),
        method='filter_loading_state'
    )
    unloading_state = django_filters.ModelChoiceFilter(
        queryset=Location.objects.filter(level=2),
        method='filter_unloading_state'
    )
    
    # Старые текстовые фильтры (для совместимости)
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
        Uses Location objects if specified, otherwise falls back to text search
        """
        if not value:
            return queryset
            
        # Получаем параметры из запроса
        request = self.request
        if not request:
            return queryset
            
        # Фильтруем по загрузке
        filtered_queryset = queryset
        
        # Проверяем если есть loading_location_id
        loading_location_id = request.query_params.get('loading_location_id')
        if loading_location_id:
            try:
                # Получаем локацию
                location = Location.objects.get(id=loading_location_id)
                if location.latitude and location.longitude:
                    # Фильтруем грузы в радиусе
                    locations_in_radius = self._get_locations_in_radius(
                        location.latitude, location.longitude, value
                    )
                    filtered_queryset = filtered_queryset.filter(
                        loading_location__in=locations_in_radius
                    )
            except Location.DoesNotExist:
                pass
                
        # Проверяем если есть unloading_location_id
        unloading_location_id = request.query_params.get('unloading_location_id')
        if unloading_location_id:
            try:
                # Получаем локацию
                location = Location.objects.get(id=unloading_location_id)
                if location.latitude and location.longitude:
                    # Фильтруем грузы в радиусе
                    locations_in_radius = self._get_locations_in_radius(
                        location.latitude, location.longitude, value
                    )
                    filtered_queryset = filtered_queryset.filter(
                        unloading_location__in=locations_in_radius
                    )
            except Location.DoesNotExist:
                pass
                
        return filtered_queryset
    
    def filter_loading_country(self, queryset, name, value):
        """Фильтр по стране загрузки"""
        if not value:
            return queryset
        
        # Ищем все Location с указанной страной
        return queryset.filter(
            Q(loading_location__country=value) |
            Q(loading_location=value)  # Если сама страна выбрана как локация
        )
    
    def filter_unloading_country(self, queryset, name, value):
        """Фильтр по стране выгрузки"""
        if not value:
            return queryset
        
        # Ищем все Location с указанной страной
        return queryset.filter(
            Q(unloading_location__country=value) |
            Q(unloading_location=value)  # Если сама страна выбрана как локация
        )
    
    def filter_loading_state(self, queryset, name, value):
        """Фильтр по региону/штату загрузки"""
        if not value:
            return queryset
        
        # Ищем все Location с указанным регионом или который является регионом
        return queryset.filter(
            Q(loading_location__parent=value) |
            Q(loading_location=value)  # Если сам штат выбран как локация
        )
    
    def filter_unloading_state(self, queryset, name, value):
        """Фильтр по региону/штату выгрузки"""
        if not value:
            return queryset
        
        # Ищем все Location с указанным регионом или который является регионом
        return queryset.filter(
            Q(unloading_location__parent=value) |
            Q(unloading_location=value)  # Если сам штат выбран как локация
        )
    
    def _get_locations_in_radius(self, lat, lon, radius_km):
        """
        Получить все локации в указанном радиусе
        Используем формулу Гаверсинуса для расчета расстояния
        """
        locations = []
        
        # Получаем все локации уровня 3 (города)
        cities = Location.objects.filter(level=3)
        
        for city in cities:
            if city.latitude and city.longitude:
                distance = self._haversine(
                    float(lat), float(lon),
                    float(city.latitude), float(city.longitude)
                )
                if distance <= radius_km:
                    locations.append(city.id)
        
        return locations
    
    def _haversine(self, lat1, lon1, lat2, lon2):
        """
        Расчет расстояния между двумя точками по формуле Гаверсинуса
        Результат в километрах
        """
        # Конвертируем градусы в радианы
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        
        # Формула Гаверсинуса
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        r = 6371  # Радиус Земли в километрах
        
        return c * r