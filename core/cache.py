from django.core.cache import cache
from django.conf import settings
from .models import Location

CACHE_TTL = getattr(settings, 'LOCATION_CACHE_TTL', 60 * 60 * 24)  # 24 hours

def get_cached_countries():
    """Get list of countries from cache or database"""
    key = 'location_countries'
    countries = cache.get(key)
    
    if countries is None:
        countries = list(Location.objects.filter(level=1).values(
            'id', 'name', 'code', 'additional_data'
        ))
        cache.set(key, countries, CACHE_TTL)
    
    return countries

def get_cached_states(country_id):
    """Get states for a country from cache or database"""
    key = f'location_states_{country_id}'
    states = cache.get(key)
    
    if states is None:
        states = list(Location.objects.filter(
            level=2,
            country_id=country_id
        ).values('id', 'name', 'code', 'additional_data'))
        cache.set(key, states, CACHE_TTL)
    
    return states

def get_cached_cities(parent_id, is_state=True):
    """Get cities for a state or country from cache or database"""
    key = f'location_cities_{parent_id}'
    cities = cache.get(key)
    
    if cities is None:
        filter_kwargs = {
            'level': 3,
            'parent_id' if is_state else 'country_id': parent_id
        }
        cities = list(Location.objects.filter(**filter_kwargs).values(
            'id', 'name', 'latitude', 'longitude'
        ))
        cache.set(key, cities, CACHE_TTL)
    
    return cities

def invalidate_location_cache(location_id=None):
    """Invalidate location caches"""
    if location_id:
        location = Location.objects.get(id=location_id)
        if location.level == 1:  # Country
            cache.delete('location_countries')
            cache.delete(f'location_states_{location_id}')
            cache.delete(f'location_cities_{location_id}')
        elif location.level == 2:  # State
            cache.delete(f'location_states_{location.country_id}')
            cache.delete(f'location_cities_{location_id}')
        else:  # City
            cache.delete(f'location_cities_{location.parent_id}')
    else:
        # Invalidate all location caches
        cache.delete_pattern('location_*')