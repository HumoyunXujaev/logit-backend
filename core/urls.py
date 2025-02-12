from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    NotificationViewSet,
    FavoriteViewSet,
    RatingViewSet,
    TelegramGroupViewSet,
    TelegramMessageViewSet,
    SearchFilterViewSet
)

router = DefaultRouter()
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'favorites', FavoriteViewSet, basename='favorite')
router.register(r'ratings', RatingViewSet, basename='rating')
router.register(r'telegram-groups', TelegramGroupViewSet)
router.register(r'telegram-messages', TelegramMessageViewSet)
router.register(r'search-filters', SearchFilterViewSet, basename='search-filter')

urlpatterns = [
    path('', include(router.urls)),
]