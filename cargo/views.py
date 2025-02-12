from rest_framework import viewsets, status, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiParameter

from users.models import User
from .models import Cargo, CarrierRequest, CargoDocument
from .serializers import (
    CargoSerializer,
    CargoListSerializer,
    CargoCreateSerializer,
    CargoUpdateSerializer,
    CargoAssignmentSerializer,
    CargoAcceptanceSerializer,
    CarrierRequestSerializer,
    CarrierRequestListSerializer,
    CarrierRequestCreateSerializer,
    CarrierRequestUpdateSerializer
)
from .filters import CargoFilter
from core.permissions import (
    IsVerifiedUser,
    IsObjectOwner,
    IsCarrier,
    IsLogisticsCompany,
    IsCargoOwner
)

class CarrierRequestViewSet(viewsets.ModelViewSet):
    """ViewSet for carrier requests"""
    queryset = CarrierRequest.objects.all()
    serializer_class = CarrierRequestSerializer
    # permission_classes = [IsVerifiedUser, IsCarrier]
    permission_classes = [IsVerifiedUser]

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter
    ]
    search_fields = [
        'loading_point', 'unloading_point',
        'carrier__username', 'notes'
    ]
    ordering_fields = ['created_at', 'ready_date']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter queryset based on user role"""
        queryset = super().get_queryset()
        user = self.request.user

        if user.role == 'carrier':
            return queryset.filter(carrier=user)
        elif user.role == 'student':
            return queryset.filter(status='pending')
        elif user.is_staff:
            return queryset
            
        return queryset.none()
    
    def get_serializer_class(self):
        """Return appropriate serializer class"""
        if self.action == 'create':
            return CarrierRequestCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return CarrierRequestUpdateSerializer
        elif self.action == 'list':
            return CarrierRequestListSerializer
        return self.serializer_class
    
    def perform_create(self, serializer):
        """Create a new carrier request"""
        serializer.save(carrier=self.request.user)

    @extend_schema(
        description='Get matching cargos for carrier request',
        responses={200: CargoListSerializer(many=True)}
    )
    @action(detail=True, methods=['get'])
    def matching_cargos(self, request, pk=None):
        """Get list of cargos matching this carrier request"""
        carrier_request = self.get_object()
        
        # Filter cargos based on matching criteria
        matching_cargos = Cargo.objects.filter(
            status='pending',
            loading_date__gte=carrier_request.ready_date,
            loading_point__icontains=carrier_request.loading_point,
            unloading_point__icontains=carrier_request.unloading_point
        )
        
        serializer = CargoListSerializer(matching_cargos, many=True)
        return Response(serializer.data)

class CargoViewSet(viewsets.ModelViewSet):
    """ViewSet for cargo management"""
    queryset = Cargo.objects.all()
    serializer_class = CargoSerializer
    permission_classes = [IsVerifiedUser]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter
    ]
    filterset_class = CargoFilter
    search_fields = [
        'title', 'description',
        'loading_point', 'unloading_point'
    ]
    ordering_fields = [
        'created_at', 'loading_date',
        'price', 'views_count'
    ]
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter queryset based on user role"""
        queryset = super().get_queryset()
        user = self.request.user

        if user.role == 'carrier':
            # Carriers see pending cargos and ones assigned to them
            return queryset.filter(
                Q(status='pending') |
                Q(assigned_to=user)
            )
        elif user.role == 'student':
            # Students see pending cargos and ones they manage
            return queryset.filter(
                Q(status='pending') |
                Q(managed_by=user)
            )
        elif user.role in ['cargo-owner', 'logistics-company']:
            # Owners see their own cargos
            return queryset.filter(owner=user)
        elif user.is_staff:
            return queryset
            
        return queryset.none()
    
    def get_serializer_class(self):
        """Return appropriate serializer class"""
        if self.action == 'create':
            return CargoCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return CargoUpdateSerializer
        elif self.action == 'list':
            return CargoListSerializer
        elif self.action == 'assign_carrier':
            return CargoAssignmentSerializer
        elif self.action == 'accept_assignment':
            return CargoAcceptanceSerializer
        return self.serializer_class
    
    def get_permissions(self):
        """Get custom permissions for different actions"""
        if self.action == 'create':
            permission_classes = [
                IsVerifiedUser,
                (IsCargoOwner | IsLogisticsCompany)
            ]
        elif self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [IsVerifiedUser, IsObjectOwner]
        else:
            permission_classes = [IsVerifiedUser]
        return [permission() for permission in permission_classes]

    @extend_schema(
        description='Get matching carrier requests for cargo',
        responses={200: CarrierRequestListSerializer(many=True)}
    )
    @action(detail=True, methods=['get'])
    def matching_carriers(self, request, pk=None):
        """Get list of carrier requests matching this cargo"""
        cargo = self.get_object()
        
        # Filter carrier requests based on matching criteria
        matching_requests = CarrierRequest.objects.filter(
            status='pending',
            ready_date__lte=cargo.loading_date,
            loading_point__icontains=cargo.loading_point,
            unloading_point__icontains=cargo.unloading_point
        )
        
        serializer = CarrierRequestListSerializer(matching_requests, many=True)
        return Response(serializer.data)

    @extend_schema(
        description='Assign cargo to carrier',
        request=CargoAssignmentSerializer,
        responses={200: CargoSerializer}
    )
    @action(detail=True, methods=['post'])
    def assign_carrier(self, request, pk=None):
        """Assign cargo to a carrier through carrier request"""
        cargo = self.get_object()
        serializer = self.get_serializer(cargo, data=request.data)
        
        if serializer.is_valid():
            cargo = serializer.save()
            return Response(CargoSerializer(cargo).data)
            
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    @extend_schema(
        description='Accept or reject cargo assignment',
        request=CargoAcceptanceSerializer,
        responses={200: CargoSerializer}
    )
    @action(detail=True, methods=['post'])
    def accept_assignment(self, request, pk=None):
        """Accept or reject cargo assignment"""
        cargo = self.get_object()
        serializer = self.get_serializer(cargo, data=request.data)
        
        if serializer.is_valid():
            cargo = serializer.save()
            return Response(CargoSerializer(cargo).data)
            
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    def perform_create(self, serializer):
        """Create a new cargo and notify relevant users"""
        cargo = serializer.save(owner=self.request.user)
        
        # Create notification for logistics students if cargo needs assignment
        if cargo.status == 'pending':
            from core.models import Notification
            # Get all logistics students
            students = User.objects.filter(role='student', is_active=True)
            
            for student in students:
                Notification.objects.create(
                    user=student,
                    type='cargo',
                    message=f'New cargo available: {cargo.title} ({cargo.loading_point} - {cargo.unloading_point})',
                    content_object=cargo
                )

    def perform_update(self, serializer):
        """Update cargo and handle notifications"""
        old_status = serializer.instance.status
        cargo = serializer.save()
        new_status = cargo.status
        
        from core.models import Notification
        
        # Handle status change notifications
        if old_status != new_status:
            # Notify owner about status changes
            Notification.objects.create(
                user=cargo.owner,
                type='cargo',
                message=f'Cargo status changed to {new_status}: {cargo.title}',
                content_object=cargo
            )
            
            # Notify assigned carrier about status changes
            if cargo.assigned_to:
                Notification.objects.create(
                    user=cargo.assigned_to,
                    type='cargo',
                    message=f'Cargo status changed to {new_status}: {cargo.title}',
                    content_object=cargo
                )
            
            # Notify managing student about status changes
            if cargo.managed_by:
                Notification.objects.create(
                    user=cargo.managed_by,
                    type='cargo',
                    message=f'Cargo status changed to {new_status}: {cargo.title}',
                    content_object=cargo
                )

    @action(detail=True, methods=['post'])
    def increment_views(self, request, pk=None):
        """Increment cargo view counter"""
        cargo = self.get_object()
        cargo.views_count += 1
        cargo.save(update_fields=['views_count'])
        return Response({'status': 'view count updated'})

    @extend_schema(
        description='Search for cargos with advanced filters',
        parameters=[
            OpenApiParameter(
                name='q',
                type=str,
                description='Search query'
            ),
            OpenApiParameter(
                name='from_location',
                type=str,
                description='Loading point'
            ),
            OpenApiParameter(
                name='to_location',
                type=str,
                description='Unloading point'
            ),
            OpenApiParameter(
                name='date_from',
                type=str,
                description='Loading date from'
            ),
            OpenApiParameter(
                name='date_to',
                type=str,
                description='Loading date to'
            ),
            OpenApiParameter(
                name='vehicle_type',
                type=str,
                description='Vehicle type'
            ),
        ],
        responses={200: CargoListSerializer(many=True)}
    )
    @action(detail=False, methods=['get'])
    def search(self, request):
        """Advanced cargo search"""
        queryset = self.get_queryset()
        
        # Apply text search
        q = request.query_params.get('q', '')
        if q:
            queryset = queryset.filter(
                Q(title__icontains=q) |
                Q(description__icontains=q)
            )
        
        # Filter by location
        from_location = request.query_params.get('from_location', '')
        if from_location:
            queryset = queryset.filter(
                loading_point__icontains=from_location
            )
            
        to_location = request.query_params.get('to_location', '')
        if to_location:
            queryset = queryset.filter(
                unloading_point__icontains=to_location
            )
        
        # Filter by date range
        date_from = request.query_params.get('date_from', '')
        if date_from:
            queryset = queryset.filter(loading_date__gte=date_from)
            
        date_to = request.query_params.get('date_to', '')
        if date_to:
            queryset = queryset.filter(loading_date__lte=date_to)
        
        # Filter by vehicle type
        vehicle_type = request.query_params.get('vehicle_type', '')
        if vehicle_type:
            queryset = queryset.filter(vehicle_type=vehicle_type)
        
        # Order results
        queryset = self.filter_queryset(queryset)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
            
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @extend_schema(
        description='Get cargo statistics',
        responses={200: {'type': 'object'}}
    )
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get cargo statistics"""
        user = request.user
        queryset = self.get_queryset()
        
        stats = {
            'total_active': queryset.filter(status='pending').count(),
            'total_in_progress': queryset.filter(status='in_progress').count(),
            'total_completed': queryset.filter(status='completed').count(),
        }
        
        if user.role == 'carrier':
            stats.update({
                'assigned_to_me': queryset.filter(assigned_to=user).count(),
                'completed_by_me': queryset.filter(
                    assigned_to=user,
                    status='completed'
                ).count(),
            })
        elif user.role == 'student':
            stats.update({
                'managed_by_me': queryset.filter(managed_by=user).count(),
                'pending_assignment': queryset.filter(
                    status='pending',
                    managed_by=None
                ).count(),
            })
        elif user.role in ['cargo-owner', 'logistics-company']:
            stats.update({
                'my_active': queryset.filter(
                    owner=user,
                    status__in=['pending', 'in_progress']
                ).count(),
                'my_completed': queryset.filter(
                    owner=user,
                    status='completed'
                ).count(),
            })
            
        return Response(stats)