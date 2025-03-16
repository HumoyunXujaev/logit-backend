from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers
from .views import (
    CargoViewSet,
    CarrierRequestViewSet,ExternalCargoViewSet,ManagerCargoViewSet
)

router = DefaultRouter()
router.register(r'cargos', CargoViewSet, basename='cargo')
router.register(r'external', ExternalCargoViewSet, basename='external-cargo')
router.register(r'carrier-requests', CarrierRequestViewSet, basename='carrier-request')
router.register(r'manager', ManagerCargoViewSet, basename='manager-cargo')

urlpatterns = [
    path('', include(router.urls)),
]