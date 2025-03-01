from math import radians, sin, cos, sqrt, atan2
from typing import List, Optional, Dict, Any
from django.db.models import Q
from core.models import Location
from core.cache import (
    get_cached_countries,
    get_cached_states,
    get_cached_cities
)

class LocationService:
    @staticmethod
    def get_location_hierarchy(location_id: int) -> List[Dict[str, Any]]:
        """Get full location hierarchy from city up to country"""
        location = Location.objects.get(id=location_id)
        return location.get_hierarchy()
    
    @staticmethod
    def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points using Haversine formula"""
        R = 6371  # Earth's radius in km
        
        lat1, lon1 = map(radians, [lat1, lon1])
        lat2, lon2 = map(radians, [lat2, lon2])
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        
        return R * c
    
    @staticmethod
    def find_locations_in_radius(
        latitude: float,
        longitude: float,
        radius: float,
        level: int = 3
    ) -> List[Dict[str, Any]]:
        """Find all locations within specified radius"""
        locations = Location.objects.filter(level=level)
        
        results = []
        for location in locations:
            if location.latitude and location.longitude:
                distance = LocationService.calculate_distance(
                    latitude, longitude,
                    float(location.latitude),
                    float(location.longitude)
                )
                if distance <= radius:
                    results.append({
                        'id': location.id,
                        'name': location.name,
                        'distance': round(distance, 2),
                        'latitude': location.latitude,
                        'longitude': location.longitude,
                        'full_name': location.full_name
                    })
        
        return sorted(results, key=lambda x: x['distance'])

    @staticmethod
    def search_locations(
        query: str,
        level: Optional[int] = None,
        country_id: Optional[int] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search locations by name with optional filters"""
        locations = Location.objects.all()
        
        if level is not None:
            locations = locations.filter(level=level)
        
        if country_id:
            locations = locations.filter(
                Q(id=country_id) |  # Country itself
                Q(country_id=country_id)  # States and cities
            )
        
        # Split query into words and create Q objects for each
        words = query.split()
        name_query = Q()
        for word in words:
            name_query |= Q(name__icontains=word)
        
        locations = locations.filter(name_query)[:limit]
        
        return [
            {
                'id': loc.id,
                'name': loc.name,
                'level': loc.level,
                'full_name': loc.full_name,
                'latitude': loc.latitude,
                'longitude': loc.longitude
            }
            for loc in locations
        ]

    @staticmethod
    def get_location_choices(
        level: int,
        parent_id: Optional[int] = None,
        country_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get location choices for dropdowns"""
        if level == 1:
            return get_cached_countries()
        elif level == 2 and country_id:
            return get_cached_states(country_id)
        elif level == 3:
            if parent_id:  # Cities of state
                return get_cached_cities(parent_id, is_state=True)
            elif country_id:  # Cities of country
                return get_cached_cities(country_id, is_state=False)
        return []

    @staticmethod
    def validate_location_path(
        city_id: Optional[int] = None,
        state_id: Optional[int] = None,
        country_id: Optional[int] = None
    ) -> bool:
        """Validate that locations form a valid path in hierarchy"""
        try:
            if city_id:
                city = Location.objects.get(id=city_id, level=3)
                if state_id and city.parent_id != state_id:
                    return False
                if country_id and city.country_id != country_id:
                    return False
                
            if state_id:
                state = Location.objects.get(id=state_id, level=2)
                if country_id and state.country_id != country_id:
                    return False
                
            return True
            
        except Location.DoesNotExist:
            return False