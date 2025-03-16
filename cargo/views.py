from decimal import Decimal
from rest_framework import viewsets, status, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from django.utils import timezone
from django.utils.dateparse import parse_date
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
    CarrierRequestUpdateSerializer,
    ManagerCargoUpdateSerializer,
    ExternalCargoCreateSerializer,
    CargoApprovalSerializer
)
from .filters import CargoFilter
from core.permissions import (
    IsVerifiedUser,
    IsManager,
    IsObjectOwner,
    isStudent,
    IsCarrier,
    IsLogisticsCompany,
    IsCargoOwner
)
import hashlib
from drf_spectacular.types import OpenApiTypes
from django.conf import settings
from rest_framework.permissions import AllowAny
import logging

logger = logging.getLogger(__name__)




class ManagerCargoViewSet(viewsets.ModelViewSet):
    """ViewSet for manager operations on cargo"""
    permission_classes = [permissions.IsAuthenticated, IsManager]
    serializer_class = ManagerCargoUpdateSerializer

    def get_queryset(self):
        """Filter queryset to show relevant cargos for managers"""
        return Cargo.objects.filter(
            Q(status=Cargo.CargoStatus.PENDING_APPROVAL) |
            Q(approved_by=self.request.user) |
            Q(status=Cargo.CargoStatus.MANAGER_APPROVED)
        ).order_by('-created_at')

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a cargo"""
        cargo = self.get_object()
        serializer = CargoApprovalSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            try:
                cargo.approve(
                    manager=request.user,
                    notes=serializer.validated_data.get('approval_notes')
                )
                return Response(
                    {'status': 'Cargo approved successfully'},
                    status=status.HTTP_200_OK
                )
            except ValueError as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject a cargo"""
        cargo = self.get_object()
        serializer = CargoApprovalSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            try:
                cargo.reject(
                    manager=request.user,
                    notes=serializer.validated_data.get('approval_notes')
                )
                return Response(
                    {'status': 'Cargo rejected successfully'},
                    status=status.HTTP_200_OK
                )
            except ValueError as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=False, methods=['get'])
    def pending_approval(self, request):
        """Get cargos pending manager approval"""
        queryset = self.get_queryset().filter(
            status=Cargo.CargoStatus.PENDING_APPROVAL
        )
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def approved(self, request):
        """Get cargos approved by the current manager"""
        queryset = self.get_queryset().filter(
            status=Cargo.CargoStatus.MANAGER_APPROVED,
            approved_by=request.user
        )
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
class ExternalCargoViewSet(viewsets.GenericViewSet):
    """ViewSet for external cargo creation via API"""
    permission_classes = [AllowAny]
    # serializer_class = CargoSerializer

    @action(detail=False, methods=['post'])
    def create_external(self, request):
        """
        Create cargo entries from external API
        Requires authentication with API key and hash verification
        """
        try:
            # Extract data from request
            api_key = request.data.get('api_key')
            created_at = request.data.get('created_at')
            received_hash = request.data.get('hash')
            orders = request.data.get('orders', [])

            # Check for required fields
            if not all([api_key, created_at, received_hash, orders]):
                return Response(
                    {'error': 'Missing required fields'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            # Verify hash
            private_key = settings.PRIVATE_API_KEY
            calculated_hash = hashlib.md5(
                (private_key + api_key + str(created_at)).encode()
            ).hexdigest()
            
            if calculated_hash != received_hash:
                return Response(
                    {'error': 'Invalid authentication'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            created_cargos = []
            errors = []
            
            # Process each order
            for order_data in orders:
                try:
                    # Convert string numeric values to proper types
                    cleaned_data = self._convert_data_types(order_data)
                    
                    # Set source type to external API if not provided
                    if 'source_type' not in cleaned_data:
                        cleaned_data['source_type'] = 'api'
                    
                    cargo = Cargo.objects.create(
                        status='pending',  # Use string to match choices
                        **cleaned_data
                    )
                    
                    created_cargos.append({
                        'id': cargo.id,
                        'title': cargo.title,
                        'source_id': cargo.source_id
                    })
                    
                except Exception as e:
                    errors.append({
                        'order': order_data.get('source_id', 'Unknown'),
                        'error': str(e)
                    })
            
            return Response(
                {
                    'status': 'success',
                    'created': len(created_cargos),
                    'errors': len(errors),
                    'cargos': created_cargos,
                    'error_details': errors
                },
                status=status.HTTP_201_CREATED
            )
            
        except Exception as e:
            return Response(
                {
                    'status': 'error',
                    'message': str(e)
                },
                status=status.HTTP_400_BAD_REQUEST
            )

    def _convert_data_types(self, data):
        """Convert string values to appropriate data types"""
        result = {}
        for key, value in data.items():
            if key in ['weight', 'volume', 'length', 'width', 'height', 'price'] and value:
                try:
                    result[key] = Decimal(str(value))
                except (ValueError, TypeError):
                    result[key] = None
            elif key == 'loading_date' and value:
                try:
                    result[key] = parse_date(str(value))
                except (ValueError, TypeError):
                    result[key] = None
            elif key in ['is_constant', 'is_ready']:
                result[key] = bool(value)
            else:
                result[key] = value
        return result
        
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
            # Carriers see pending and assigned cargos
            return queryset.filter(
                Q(status=Cargo.CargoStatus.PENDING) |
                Q(assigned_to=user)
            )
        elif user.role == 'student':
            # Students see manager-approved cargos
            # VIP students see all approved cargos, standard students see limited ones
            base_query = Q(status=Cargo.CargoStatus.MANAGER_APPROVED)
            if user.tariff == 'standard':
                 return queryset.filter(
                Q(status='pending') |
                Q(managed_by=user) | 
                Q(owner=user)
            )
            if user.tariff == 'vip':
                return queryset.filter(
                Q(status='pending') |
                Q(managed_by=user) | 
                Q(owner=user) | 
                Q(status=Cargo.CargoStatus.MANAGER_APPROVED)
            )
                # return queryset.filter(base_query)
            
            else:
                return queryset.none()

        elif user.role == 'cargo-owner':
            # Owners see their own cargos
            return queryset.filter(owner=user)
        elif user.role == 'logistics-company':
            # Companies see their own cargos
            return queryset.filter(owner=user)
        elif user.role == 'manager':
            # Managers see all cargos
            return queryset
        elif user.is_staff:
            return queryset
            
        return queryset.none()
            
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
                (IsCargoOwner | IsLogisticsCompany | isStudent)
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
        """Create cargo and handle notifications"""
        cargo = serializer.save(owner=self.request.user)

        # Create notifications based on cargo status
        if cargo.status == Cargo.CargoStatus.PENDING_APPROVAL:
            self.notify_managers(cargo)
        elif cargo.status == Cargo.CargoStatus.MANAGER_APPROVED:
            self.notify_students(cargo)

    def notify_managers(self, cargo):
        """Notify managers about new cargo requiring approval"""
        from core.models import Notification
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        managers = User.objects.filter(role='manager', is_active=True)
        for manager in managers:
            Notification.objects.create(
                user=manager,
                type='cargo',
                message=f'New cargo requires approval: {cargo.title}',
                content_object=cargo
            )

    def notify_students(self, cargo):
        """Notify students about new approved cargo"""
        from core.models import Notification
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        students = User.objects.filter(role='student', is_active=True)
        for student in students:
            Notification.objects.create(
                user=student,
                type='cargo',
                message=f'New cargo available: {cargo.title}',
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
                name='loading_location_id',
                type=int,
                description='Loading location ID'
            ),
            OpenApiParameter(
                name='unloading_location_id',
                type=int,
                description='Unloading location ID'
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
            OpenApiParameter(
                name='radius',
                type=int,
                description='Search radius in kilometers'
            ),
        ],
        responses={200: CargoListSerializer(many=True)}
    )
    @action(detail=False, methods=['get'])
    def search(self, request):
        """Advanced cargo search"""
        queryset = self.get_queryset()
        # print the whole request
        print(request.query_params)
        
        # Apply text search
        q = request.query_params.get('q', '')
        if q:
            queryset = queryset.filter(
                Q(title__icontains=q) |
                Q(description__icontains=q)
            )
        
        # Get radius parameter
        radius = request.query_params.get('radius', None)
        if radius:
            try:
                radius = int(radius)
            except (ValueError, TypeError):
                radius = None
        
        # Filter by location ID with radius support
        loading_location_id = request.query_params.get('loading_location_id', '')
        if loading_location_id:
            try:
                from core.models import Location
                from django.db.models import Q
                
                # Проверяем, существует ли локация
                location = Location.objects.filter(id=loading_location_id).first()
                
                if location and radius and location.latitude and location.longitude:
                    # Get all locations within radius
                    from core.services.location import LocationService
                    locations_in_radius = LocationService.find_locations_in_radius(
                        float(location.latitude),
                        float(location.longitude),
                        radius
                    )
                    location_ids = [loc['id'] for loc in locations_in_radius]
                    
                    if location_ids:
                        queryset = queryset.filter(
                            Q(loading_location__in=location_ids) |
                            Q(loading_location=location.id)
                        )
                else:
                    # Direct location match
                    queryset = queryset.filter(loading_location=loading_location_id)
            except Exception as e:
                logger.error(f"Error in loading_location search: {str(e)}")
                # Fallback to text search if location not found or error occurs
                pass
        
        unloading_location_id = request.query_params.get('unloading_location_id', '')
        if unloading_location_id:
            try:
                from core.models import Location
                from django.db.models import Q
                
                # Проверяем, существует ли локация
                location = Location.objects.filter(id=unloading_location_id).first()
                
                if location and radius and location.latitude and location.longitude:
                    # Get all locations within radius
                    from core.services.location import LocationService
                    locations_in_radius = LocationService.find_locations_in_radius(
                        float(location.latitude),
                        float(location.longitude),
                        radius
                    )
                    location_ids = [loc['id'] for loc in locations_in_radius]
                    
                    if location_ids:
                        queryset = queryset.filter(
                            Q(unloading_location__in=location_ids) |
                            Q(unloading_location=location.id)
                        )
                else:
                    # Direct location match
                    queryset = queryset.filter(unloading_location=unloading_location_id)
            except Exception as e:
                logger.error(f"Error in unloading_location search: {str(e)}")
                # Fallback to text search if location not found or error occurs
                pass
        
        # Filter by text location (for backward compatibility)
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