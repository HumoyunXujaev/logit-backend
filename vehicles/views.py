from rest_framework import viewsets, status, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiParameter
from .models import (
    Vehicle,
    VehicleDocument,
    VehicleAvailability,
    VehicleInspection
)
from .serializers import (
    VehicleSerializer,
    VehicleListSerializer,
    VehicleCreateSerializer,
    VehicleUpdateSerializer,
    VehicleVerificationSerializer,
    VehicleDocumentSerializer,
    VehicleAvailabilitySerializer,
    VehicleInspectionSerializer
)
from .filters import VehicleFilter
from core.permissions import (
    IsVerifiedUser,
    IsObjectOwner,
    IsCarrier
)

class VehicleViewSet(viewsets.ModelViewSet):
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer
    permission_classes = [IsVerifiedUser, IsCarrier]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter
    ]
    filterset_class = VehicleFilter
    search_fields = [
        'registration_number',
        'owner__username'
    ]
    ordering_fields = [
        'created_at',
        'capacity',
        'volume'
    ]
    ordering = ['-created_at']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.is_staff:
            # Regular users can only see their own vehicles
            return queryset.filter(owner=self.request.user)
        return queryset
    
    def get_serializer_class(self):
        if self.action == 'create':
            return VehicleCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return VehicleUpdateSerializer
        elif self.action == 'list':
            return VehicleListSerializer
        elif self.action == 'verify':
            return VehicleVerificationSerializer
        return self.serializer_class
    
    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [IsVerifiedUser, IsCarrier, IsObjectOwner]
        else:
            permission_classes = [IsVerifiedUser, IsCarrier]
        return [permission() for permission in permission_classes]
    
    @extend_schema(
        description='Verify vehicle',
        request=VehicleVerificationSerializer,
        responses={200: VehicleSerializer}
    )
    @action(
        detail=True,
        methods=['post'],
        permission_classes=[permissions.IsAdminUser]
    )
    def verify(self, request, pk=None):
        """Verify vehicle (admin only)"""
        vehicle = self.get_object()
        serializer = self.get_serializer(
            vehicle,
            data=request.data,
            partial=True,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        vehicle = serializer.save()
        
        return Response(
            VehicleSerializer(vehicle).data
        )
    
    @extend_schema(
        description='Add document to vehicle',
        request=VehicleDocumentSerializer,
        responses={201: VehicleDocumentSerializer}
    )
    @action(detail=True, methods=['post'])
    def add_document(self, request, pk=None):
        """Add document to vehicle"""
        vehicle = self.get_object()
        serializer = VehicleDocumentSerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save(vehicle=vehicle)
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @extend_schema(
        description='Get vehicle documents',
        responses={200: VehicleDocumentSerializer(many=True)}
    )
    @action(detail=True, methods=['get'])
    def documents(self, request, pk=None):
        """Get all documents for a vehicle"""
        vehicle = self.get_object()
        documents = VehicleDocument.objects.filter(vehicle=vehicle)
        serializer = VehicleDocumentSerializer(documents, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        description='Set vehicle availability',
        request=VehicleAvailabilitySerializer,
        responses={201: VehicleAvailabilitySerializer}
    )
    @action(detail=True, methods=['post'])
    def set_availability(self, request, pk=None):
        """Set vehicle availability"""
        vehicle = self.get_object()
        serializer = VehicleAvailabilitySerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save(vehicle=vehicle)
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @extend_schema(
        description='Get vehicle availability',
        responses={200: VehicleAvailabilitySerializer(many=True)}
    )
    @action(detail=True, methods=['get'])
    def availability(self, request, pk=None):
        """Get vehicle availability periods"""
        vehicle = self.get_object()
        availability = VehicleAvailability.objects.filter(
            vehicle=vehicle,
            end_date__gte=timezone.now().date()
        )
        serializer = VehicleAvailabilitySerializer(
            availability,
            many=True
        )
        return Response(serializer.data)
    
    @extend_schema(
        description='Add inspection record',
        request=VehicleInspectionSerializer,
        responses={201: VehicleInspectionSerializer}
    )
    @action(detail=True, methods=['post'])
    def add_inspection(self, request, pk=None):
        """Add inspection record"""
        vehicle = self.get_object()
        serializer = VehicleInspectionSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            serializer.save(
                vehicle=vehicle,
                inspector=request.user
            )
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @extend_schema(
        description='Get inspection records',
        responses={200: VehicleInspectionSerializer(many=True)}
    )
    @action(detail=True, methods=['get'])
    def inspections(self, request, pk=None):
        """Get vehicle inspection records"""
        vehicle = self.get_object()
        inspections = VehicleInspection.objects.filter(
            vehicle=vehicle
        )
        serializer = VehicleInspectionSerializer(
            inspections,
            many=True
        )
        return Response(serializer.data)

class VehicleDocumentViewSet(viewsets.ModelViewSet):
    serializer_class = VehicleDocumentSerializer
    permission_classes = [IsVerifiedUser, IsCarrier]
    
    def get_queryset(self):
        return VehicleDocument.objects.filter(
            vehicle__owner=self.request.user
        )
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def perform_create(self, serializer):
        vehicle_id = self.kwargs.get('vehicle_pk')
        vehicle = Vehicle.objects.get(id=vehicle_id)
        if vehicle.owner != self.request.user:
            raise permissions.PermissionDenied(
                'You do not have permission to add documents to this vehicle'
            )
        serializer.save(vehicle=vehicle)
    
    @extend_schema(
        description='Verify document',
        request=None,
        responses={200: VehicleDocumentSerializer}
    )
    @action(
        detail=True,
        methods=['post'],
        permission_classes=[permissions.IsAdminUser]
    )
    def verify(self, request, pk=None):
        """Verify document (admin only)"""
        document = self.get_object()
        document.verified = True
        document.verified_at = timezone.now()
        document.verified_by = request.user
        document.save()
        
        serializer = self.get_serializer(document)
        return Response(serializer.data)