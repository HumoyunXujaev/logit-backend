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