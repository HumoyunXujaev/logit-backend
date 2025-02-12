from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers
from .views import (
    CargoViewSet,
    CarrierRequestViewSet
)

router = DefaultRouter()
router.register(r'cargos', CargoViewSet, basename='cargo')
router.register(r'carrier-requests', CarrierRequestViewSet, basename='carrier-request')

urlpatterns = [
    path('', include(router.urls)),
]