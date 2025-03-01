from rest_framework import viewsets, status, permissions,filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiParameter
from .models import (
    Notification, Favorite, Rating, TelegramGroup,
    TelegramMessage, SearchFilter
)
from .serializers import (
    NotificationSerializer, FavoriteSerializer, RatingSerializer,
    RatingCreateSerializer, TelegramGroupSerializer,
    TelegramMessageSerializer, SearchFilterSerializer,
    SearchFilterUpdateSerializer
)
from .permissions import IsVerifiedUser, IsStaffOrReadOnly
from django.db.models import F, FloatField
from django.db.models.functions import Power, Sqrt
from django.contrib.postgres.search import SearchVector, SearchQuery
from .models import Location
from .serializers import (
    LocationListSerializer,
    LocationDetailSerializer,
    LocationSearchSerializer
)

class LocationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Location.objects.all()
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return LocationListSerializer
        if self.action in ['nearest', 'search']:
            return LocationSearchSerializer
        return LocationDetailSerializer

    @action(detail=False)
    def countries(self, request):
        """Get list of countries"""
        countries = Location.objects.filter(level=1)
        serializer = self.get_serializer(countries, many=True)
        return Response(serializer.data)

    @action(detail=False)
    def states(self, request):
        """Get states/regions for a country"""
        country_id = request.query_params.get('country_id')
        if not country_id:
            return Response({'error': 'country_id parameter is required'}, status=400)
            
        states = Location.objects.filter(
            level=2,
            country_id=country_id
        )
        serializer = self.get_serializer(states, many=True)
        return Response(serializer.data)

    @action(detail=False)
    def cities(self, request):
        """Get cities for a state or country"""
        state_id = request.query_params.get('state_id')
        country_id = request.query_params.get('country_id')
        
        if not (state_id or country_id):
            return Response(
                {'error': 'Either state_id or country_id parameter is required'},
                status=400
            )
            
        cities = Location.objects.filter(level=3)
        if state_id:
            cities = cities.filter(parent_id=state_id)
        elif country_id:
            cities = cities.filter(country_id=country_id)
            
        serializer = self.get_serializer(cities, many=True)
        return Response(serializer.data)

    @action(detail=False)
    def nearest(self, request):
        """Find locations within specified radius"""
        try:
            lat = float(request.query_params.get('lat', 0))
            lon = float(request.query_params.get('lon', 0))
            radius = float(request.query_params.get('radius', 100))  # km
            level = int(request.query_params.get('level', 3))  # Default to cities
        except (TypeError, ValueError):
            return Response({'error': 'Invalid parameters'}, status=400)

        # Calculate distances using the Haversine formula approximation
        # This formula works well for PostgreSQL
        locations = Location.objects.filter(level=level).annotate(
            distance=Sqrt(
                Power(69.1 * (F('latitude') - lat), 2) +
                Power(69.1 * (F('longitude') - lon) * 0.73, 2)
            ).annotate(distance=FloatField())
        ).filter(distance__lte=radius).order_by('distance')

        serializer = self.get_serializer(locations, many=True)
        return Response(serializer.data)

    @action(detail=False)
    def search(self, request):
        """Search locations by name with full text search"""
        query = request.query_params.get('q', '')
        if not query:
            return Response({'error': 'Search query is required'}, status=400)

        locations = Location.objects.annotate(
            search=SearchVector('name')
        ).filter(search=SearchQuery(query))

        serializer = self.get_serializer(locations, many=True)
        return Response(serializer.data)

    @action(detail=True)
    def children(self, request, pk=None):
        """Get direct child locations"""
        location = self.get_object()
        children = Location.objects.filter(parent=location)
        serializer = self.get_serializer(children, many=True)
        return Response(serializer.data)
    
class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)
    
    @extend_schema(
        description='Mark notification as read',
        responses={200: {'description': 'Notification marked as read'}}
    )
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return Response({'status': 'notification marked as read'})
    
    @extend_schema(
        description='Mark all notifications as read',
        responses={200: {'description': 'All notifications marked as read'}}
    )
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        self.get_queryset().update(is_read=True)
        return Response({'status': 'all notifications marked as read'})
    
    @extend_schema(
        description='Delete all notifications',
        responses={200: {'description': 'All notifications deleted'}}
    )
    @action(detail=False, methods=['delete'])
    def delete_all(self, request):
        self.get_queryset().delete()
        return Response({'status': 'all notifications deleted'})

class FavoriteViewSet(viewsets.ModelViewSet):
    serializer_class = FavoriteSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Favorite.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @extend_schema(
        description='Clear all favorites',
        responses={200: {'description': 'All favorites cleared'}}
    )
    @action(detail=False, methods=['delete'])
    def clear_all(self, request):
        self.get_queryset().delete()
        return Response({'status': 'all favorites cleared'})

class RatingViewSet(viewsets.ModelViewSet):
    permission_classes = [IsVerifiedUser]
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return RatingCreateSerializer
        return RatingSerializer
    
    def get_queryset(self):
        if self.action == 'list':
            # Show ratings given to or by the current user
            return Rating.objects.filter(
                Q(from_user=self.request.user) |
                Q(to_user=self.request.user)
            )
        return Rating.objects.all()
    
    def perform_create(self, serializer):
        serializer.save(from_user=self.request.user)

class TelegramGroupViewSet(viewsets.ModelViewSet):
    queryset = TelegramGroup.objects.all()
    serializer_class = TelegramGroupSerializer
    permission_classes = [IsStaffOrReadOnly]
    
    @extend_schema(
        description='Sync messages from group',
        responses={200: {'description': 'Group sync initiated'}}
    )
    @action(detail=True, methods=['post'])
    def sync(self, request, pk=None):
        group = self.get_object()
        # Start celery task for syncing
        from .tasks import sync_telegram_group
        sync_telegram_group.delay(group.id)
        return Response({'status': 'sync initiated'})

class TelegramMessageViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = TelegramMessage.objects.all()
    serializer_class = TelegramMessageSerializer
    permission_classes = [IsStaffOrReadOnly]
    
    @extend_schema(
        description='Process message',
        responses={200: {'description': 'Message processed'}}
    )
    @action(detail=True, methods=['post'])
    def process(self, request, pk=None):
        message = self.get_object()
        if message.processed:
            return Response(
                {'detail': 'Message already processed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Start celery task for processing
        from .tasks import process_telegram_message
        process_telegram_message.delay(message.id)
        return Response({'status': 'processing initiated'})

class SearchFilterViewSet(viewsets.ModelViewSet):
    serializer_class = SearchFilterSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return SearchFilter.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        if self.action in ['update', 'partial_update']:
            return SearchFilterUpdateSerializer
        return self.serializer_class
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @extend_schema(
        description='Toggle notifications for filter',
        responses={200: {'description': 'Notifications toggled'}}
    )
    @action(detail=True, methods=['post'])
    def toggle_notifications(self, request, pk=None):
        filter_obj = self.get_object()
        filter_obj.notifications_enabled = not filter_obj.notifications_enabled
        filter_obj.save()
        return Response({
            'status': 'notifications ' +
            ('enabled' if filter_obj.notifications_enabled else 'disabled')
        })