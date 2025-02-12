from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers
from .views import (
    VehicleViewSet,
    VehicleDocumentViewSet
)

router = DefaultRouter()
router.register(r'', VehicleViewSet, basename='vehicle')

vehicle_router = routers.NestedDefaultRouter(
    router,
    r'',
    lookup='vehicle'
)
vehicle_router.register(
    r'documents',
    VehicleDocumentViewSet,
    basename='vehicle-documents'
)

urlpatterns = [
    path('', include(router.urls)),
    path('', include(vehicle_router.urls)),
]