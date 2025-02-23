from rest_framework import serializers
from django.utils import timezone
from .models import CargoStatusHistory
from users.serializers import UserProfileSerializer
from .models import Cargo, CarrierRequest, CargoDocument
from vehicles.serializers import VehicleSerializer
from django.conf import settings

class CargoApprovalSerializer(serializers.ModelSerializer):
    """Serializer for manager approval/rejection of cargo"""
    approval_notes = serializers.CharField(required=False, allow_blank=True)
    
    class Meta:
        model = Cargo
        fields = ['approval_notes']

    def validate(self, data):
        user = self.context['request'].user
        if user.role != 'manager':
            raise serializers.ValidationError(
                "Only managers can perform this action"
            )
        return data

class ManagerCargoUpdateSerializer(serializers.ModelSerializer):
    """Serializer for managers to update cargo details"""
    class Meta:
        model = Cargo
        fields = [
            'title', 'description', 'weight',
            'volume', 'length', 'width', 'height',
            'loading_point', 'unloading_point',
            'additional_points', 'loading_date',
            'is_constant', 'is_ready', 'vehicle_type',
            'loading_type', 'payment_method', 'price',
            'payment_details', 'status'
        ]

    def validate_status(self, value):
        if value not in [
            Cargo.CargoStatus.MANAGER_APPROVED,
            Cargo.CargoStatus.REJECTED,
            Cargo.CargoStatus.PENDING
        ]:
            raise serializers.ValidationError(
                "Invalid status for manager update"
            )
        return value

    def validate(self, data):
        user = self.context['request'].user
        if user.role != 'manager':
            raise serializers.ValidationError(
                "Only managers can update cargo details"
            )
        return data
    
class ExternalCargoCreateSerializer(serializers.ModelSerializer):
    """Serializer for external cargo creation with API key validation"""
    api_key = serializers.CharField(write_only=True)
    source_type = serializers.ChoiceField(choices=Cargo.SourceType.choices)
    source_id = serializers.CharField(required=True)

    class Meta:
        model = Cargo
        fields = [
            'title', 'description', 'weight',
            'volume', 'length', 'width', 'height',
            'loading_point', 'unloading_point',
            'additional_points', 'loading_date',
            'is_constant', 'is_ready', 'vehicle_type',
            'loading_type', 'payment_method', 'price',
            'payment_details', 'source_type', 'source_id',
            'api_key'
        ]

    def validate_api_key(self, value):
        """Validate the API key against the configured value"""
        valid_key = getattr(settings, 'EXTERNAL_API_KEY', None)
        if not valid_key:
            raise serializers.ValidationError(
                "API key validation is not configured"
            )
        
        if value != valid_key:
            raise serializers.ValidationError("Invalid API key")
        
        return value

    def validate(self, data):
        """Additional validation for the complete cargo data"""
        # Remove api_key from data before saving
        data.pop('api_key', None)
        
        # Set status to pending for external cargos
        data['status'] = 'pending'
        
        return data
    
class CargoDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = CargoDocument
        fields = [
            'id', 'type', 'title', 'file',
            'uploaded_at', 'notes'
        ]
        read_only_fields = ['uploaded_at']

class CargoStatusHistorySerializer(serializers.ModelSerializer):
    changed_by = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = CargoStatusHistory
        fields = [
            'id', 'status', 'changed_by',
            'changed_at', 'comment'
        ]
        read_only_fields = ['changed_at']

class CarrierRequestSerializer(serializers.ModelSerializer):
    """Full carrier request serializer with all details"""
    carrier = UserProfileSerializer(read_only=True)
    assigned_by = UserProfileSerializer(read_only=True)
    vehicle = VehicleSerializer(read_only=True)
    assigned_cargo = serializers.PrimaryKeyRelatedField(read_only=True)
    
    class Meta:
        model = CarrierRequest
        fields = [
            'id', 'carrier', 'vehicle', 'loading_point',
            'unloading_point', 'ready_date', 'vehicle_count',
            'price_expectation', 'payment_terms', 'notes',
            'status', 'created_at', 'updated_at',
            'assigned_cargo', 'assigned_by', 'assigned_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'assigned_at']

class CarrierRequestCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating carrier requests"""
    class Meta:
        model = CarrierRequest
        fields = [
            'vehicle', 'loading_point', 'unloading_point',
            'ready_date', 'vehicle_count', 'price_expectation',
            'payment_terms', 'notes'
        ]
    
    def validate_vehicle(self, value):
        """Validate that vehicle belongs to the carrier"""
        user = self.context['request'].user
        if value.owner != user:
            raise serializers.ValidationError(
                "You can only use your own vehicles"
            )
        return value

    def validate_ready_date(self, value):
        """Validate ready date is not in the past"""
        if value < timezone.now().date():
            raise serializers.ValidationError(
                "Ready date cannot be in the past"
            )
        return value

class CarrierRequestUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating carrier requests"""
    class Meta:
        model = CarrierRequest
        fields = [
            'vehicle', 'loading_point', 'unloading_point',
            'ready_date', 'vehicle_count', 'price_expectation',
            'payment_terms', 'notes', 'status'
        ]

    def validate_status(self, value):
        """Validate status transitions"""
        instance = getattr(self, 'instance', None)
        if instance:
            valid_transitions = {
                'pending': ['cancelled'],
                'assigned': ['accepted', 'rejected'],
                'accepted': ['completed', 'cancelled'],
                'rejected': ['pending'],  # Allow retry
                'completed': [],  # No transitions from completed
                'cancelled': ['pending'],  # Allow reactivation
            }
            
            current_status = instance.status
            if value != current_status and value not in valid_transitions[current_status]:
                raise serializers.ValidationError(
                    f"Cannot transition from {current_status} to {value}"
                )
                
        return value

class CarrierRequestListSerializer(serializers.ModelSerializer):
    """Simplified carrier request serializer for list views"""
    carrier = UserProfileSerializer(read_only=True)
    vehicle = VehicleSerializer(read_only=True)
    
    class Meta:
        model = CarrierRequest
        fields = [
            'id', 'carrier', 'vehicle', 'loading_point',
            'unloading_point', 'ready_date', 'vehicle_count',
            'price_expectation', 'payment_terms', 'notes',
            'status', 'created_at', 'updated_at',
            'assigned_cargo', 'assigned_by', 'assigned_at'
        ]

class CargoSerializer(serializers.ModelSerializer):
    """Full cargo serializer with all details"""
    owner = UserProfileSerializer(read_only=True)
    assigned_to = UserProfileSerializer(read_only=True)
    managed_by = UserProfileSerializer(read_only=True)
    carrier_requests = CarrierRequestListSerializer(many=True, read_only=True)

    class Meta:
        model = Cargo
        fields = [
            'id', 'title', 'description', 'status',
            'weight', 'volume', 'length', 'width', 'height',
            'loading_point', 'unloading_point', 'additional_points',
            'loading_date', 'is_constant', 'is_ready',
            'vehicle_type', 'loading_type',
            'payment_method', 'price', 'payment_details',
            'owner', 'assigned_to', 'managed_by',
            'created_at', 'updated_at', 'views_count',
            'source_type', 'source_id', 'carrier_requests'
        ]
        read_only_fields = [
            'created_at', 'updated_at', 'views_count',
            'carrier_requests'
        ]

class CargoCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating cargos"""
    class Meta:
        model = Cargo
        fields = [
            'title', 'description', 'weight',
            'volume', 'length', 'width', 'height',
            'loading_point', 'unloading_point',
            'additional_points', 'loading_date',
            'is_constant', 'is_ready', 'vehicle_type',
            'loading_type', 'payment_method', 'price',
            'payment_details'
        ]

    def validate_loading_date(self, value):
        """Validate that loading date is not in the past"""
        if value < timezone.now().date():
            raise serializers.ValidationError(
                "Loading date cannot be in the past"
            )
        return value
    
    # def create(self, validated_data):
    #     """Create cargo with default status based on user role"""
    #     user = self.context['request'].user
    #     status = 'draft'
        
    #     # Set initial status based on user role
    #     if user.role in ['cargo-owner', 'logistics-company']:
    #         status = 'pending'  # Needs logist assignment
    #     elif user.role == 'student':
    #         status = 'pending'  # Ready for carrier assignment
    #         validated_data['managed_by'] = user
            
    #     return Cargo.objects.create(
    #         owner=user,
    #         status=status,
    #         **validated_data
    #     )

    # def create(self, validated_data):
    #     """Create cargo with default status based on user role"""
    #     user = self.context['request'].user
        
    #     # Set initial status based on user role
    #     if user.role == 'cargo-owner':
    #         status = 'draft'  # Needs manager approval
    #     elif user.role == 'logistics-company':
    #         status = 'pending'  # Goes directly to students
    #     else:
    #         status = 'draft'  # Default status
            
    #     print(validated_data)
    #     print(user)
    #     validated_data.pop('owner', None)
    #     return Cargo.objects.create(
    #         owner=user,
    #         status=status,
    #         **validated_data
    #     )
    def create(self, validated_data):
        """Create cargo with appropriate initial status based on user role"""
        request = self.context.get('request')
        user = request.user if request else None

        if not user:
            raise serializers.ValidationError("User is required")

        # Set initial status based on user role
        if user.role == 'cargo-owner':
            # Cargo owners' submissions need manager approval
            validated_data['status'] = Cargo.CargoStatus.PENDING_APPROVAL
        elif user.role == 'logistics-company':
            # Logistics companies' submissions go directly to pending
            validated_data['status'] = Cargo.CargoStatus.PENDING
        elif user.role == 'manager':
            # Managers' submissions are automatically approved
            validated_data['status'] = Cargo.CargoStatus.MANAGER_APPROVED
            validated_data['approved_by'] = user
        else:
            validated_data['status'] = Cargo.CargoStatus.DRAFT

        return super().create(validated_data)
    
class CargoUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating cargo"""
    class Meta:
        model = Cargo
        fields = [
            'title', 'description', 'weight',
            'volume', 'length', 'width', 'height',
            'loading_point', 'unloading_point',
            'additional_points', 'loading_date',
            'is_constant', 'is_ready', 'vehicle_type',
            'loading_type', 'payment_method', 'price',
            'payment_details', 'status'
        ]

    def validate_status(self, value):
        """Validate status transitions based on user role"""
        user = self.context['request'].user
        instance = self.instance
        current_status = instance.status

        valid_transitions = {
            'draft': ['pending', 'cancelled'],
            'pending': ['assigned', 'cancelled'],
            'assigned': ['in_progress', 'cancelled'],
            'in_progress': ['completed', 'cancelled'],
            'completed': [],  # No transitions from completed
            'cancelled': ['draft'],  # Allow reactivation
            'expired': ['draft']  # Allow reactivation
        }

        # Additional role-based validation
        if user.role == 'student':
            if current_status == 'pending' and value == 'assigned':
                # Check if carrier is assigned
                if not self.instance.assigned_to:
                    raise serializers.ValidationError(
                        "Cannot mark as assigned without carrier"
                    )
        elif user.role == 'carrier':
            # Carriers can only update status of assigned cargos
            if instance.assigned_to != user:
                raise serializers.ValidationError(
                    "You can only update status of cargos assigned to you"
                )
            # Carriers can only mark as in_progress or completed
            if value not in ['in_progress', 'completed']:
                raise serializers.ValidationError(
                    "Invalid status transition for carrier"
                )

        if value != current_status and value not in valid_transitions[current_status]:
            raise serializers.ValidationError(
                f"Cannot transition from {current_status} to {value}"
            )

        return value

class CargoListSerializer(serializers.ModelSerializer):
    """Simplified cargo serializer for list views"""
    owner = UserProfileSerializer(read_only=True)
    assigned_to = UserProfileSerializer(read_only=True)
    managed_by = UserProfileSerializer(read_only=True)
    carrier_requests = CarrierRequestListSerializer(many=True, read_only=True)

    class Meta:
        model = Cargo
        fields = [
            # 'id', 'title', 'status', 'weight',
            # 'loading_point', 'unloading_point',
            # 'loading_date', 'vehicle_type',
            # 'payment_method', 'price', 'owner',
            # 'assigned_to', 'managed_by', 'created_at'
            'id', 'title', 'description', 'status',
            'weight', 'volume', 'length', 'width', 'height',
            'loading_point', 'unloading_point', 'additional_points',
            'loading_date', 'is_constant', 'is_ready',
            'vehicle_type', 'loading_type',
            'payment_method', 'price', 'payment_details',
            'owner', 'assigned_to', 'managed_by',
            'created_at', 'updated_at', 'views_count',
            'source_type', 'source_id', 'carrier_requests'
        ]
        read_only_fields = [
            'created_at', 'updated_at', 'views_count',
            'carrier_requests'
        ]

class CargoAssignmentSerializer(serializers.ModelSerializer):
    """Serializer for assigning cargo to carrier"""
    carrier_request = serializers.PrimaryKeyRelatedField(
        queryset=CarrierRequest.objects.filter(status='pending')
    )

    class Meta:
        model = Cargo
        fields = ['carrier_request']

    def validate_carrier_request(self, value):
        """Validate carrier request can be assigned"""
        if value.status != 'pending':
            raise serializers.ValidationError(
                "Can only assign pending carrier requests"
            )
        if value.assigned_cargo:
            raise serializers.ValidationError(
                "Carrier request already assigned to another cargo"
            )
        return value

    def update(self, instance, validated_data):
        """Assign cargo to carrier"""
        carrier_request = validated_data['carrier_request']
        user = self.context['request'].user

        # Update cargo
        instance.status = 'assigned'
        instance.assigned_to = carrier_request.carrier
        instance.managed_by = user
        instance.save()

        # Update carrier request
        carrier_request.status = 'assigned'
        carrier_request.assigned_cargo = instance
        carrier_request.assigned_by = user
        carrier_request.assigned_at = timezone.now()
        carrier_request.save()

        return instance

class CargoAcceptanceSerializer(serializers.ModelSerializer):
    """Serializer for accepting/rejecting cargo assignment"""
    decision = serializers.ChoiceField(choices=['accept', 'reject'])

    class Meta:
        model = Cargo
        fields = ['decision']

    def validate(self, data):
        """Validate user can accept/reject cargo"""
        user = self.context['request'].user
        instance = self.instance

        if instance.assigned_to != user:
            raise serializers.ValidationError(
                "You can only accept/reject cargos assigned to you"
            )
        if instance.status != 'assigned':
            raise serializers.ValidationError(
                "Can only accept/reject assigned cargos"
            )

        return data

    def update(self, instance, validated_data):
        """Process cargo acceptance/rejection"""
        decision = validated_data['decision']
        carrier_request = instance.carrier_requests.filter(status='assigned').first()

        if decision == 'accept':
            instance.status = 'in_progress'
            if carrier_request:
                carrier_request.status = 'accepted'
        else:
            instance.status = 'pending'
            instance.assigned_to = None
            if carrier_request:
                carrier_request.status = 'rejected'
                carrier_request.assigned_cargo = None

        instance.save()
        if carrier_request:
            carrier_request.save()

        return instance

# class CargoSearchSerializer(serializers.Serializer):
#     """Serializer for cargo search parameters"""
#     q = serializers.CharField(required=False, allow_blank=True)
#     from_location = serializers.CharField(required=False)
#     to_location = serializers.CharField(required=False)
#     min_weight = serializers.DecimalField(
#         required=False,
#         max_digits=10,
#         decimal_places=2
#     )
#     max_weight = serializers.DecimalField(
#         required=False,
#         max_digits=10,
#         decimal_places=2
#     )
#     date_from = serializers.DateField(required=False)
#     date_to = serializers.DateField(required=False)
#     vehicle_types = serializers.MultipleChoiceField(
#         required=False,
#         choices=Cargo.VehicleType.choices
#     )
#     loading_types = serializers.MultipleChoiceField(
#         required=False,
#         choices=Cargo.LoadingType.choices
#     )
#     payment_methods = serializers.MultipleChoiceField(
#         required=False,
#         choices=Cargo.PaymentMethod.choices
#     )
    
#     def validate(self, data):
#         """Validate search parameters"""
#         if data.get('min_weight') and data.get('max_weight'):
#             if data['min_weight'] > data['max_weight']:
#                 raise serializers.ValidationError(
#                     "min_weight cannot be greater than max_weight"
#                 )
        
#         if data.get('date_from') and data.get('date_to'):
#             if data['date_from'] > data['date_to']:
#                 raise serializers.ValidationError(
#                     "date_from cannot be later than date_to"
#                 )
        
#         return data
