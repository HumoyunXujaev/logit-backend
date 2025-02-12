from rest_framework import serializers
from django.utils import timezone
from .models import (
    Vehicle,
    VehicleDocument,
    VehicleAvailability,
    VehicleInspection
)
from users.serializers import UserProfileSerializer

class VehicleDocumentSerializer(serializers.ModelSerializer):
    verified_by = UserProfileSerializer(read_only=True)
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = VehicleDocument
        fields = [
            'id', 'type', 'title', 'file', 'file_url',
            'uploaded_at', 'expiry_date',
            'verified', 'verified_at', 'verified_by',
            'verification_notes'
        ]
        read_only_fields = [
            'uploaded_at', 'verified',
            'verified_at', 'verified_by'
        ]

    def get_file_url(self, obj):
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
        return None
    
    def validate_expiry_date(self, value):
        """Check that expiry date is not in the past"""
        if value and value < timezone.now().date():
            raise serializers.ValidationError(
                "Expiry date cannot be in the past"
            )
        return value

class VehicleInspectionSerializer(serializers.ModelSerializer):
    inspector = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = VehicleInspection
        fields = [
            'id', 'type', 'inspection_date',
            'expiry_date', 'inspector', 'result',
            'notes', 'created_at'
        ]
        read_only_fields = ['created_at']
    
    def validate(self, data):
        """
        Check that inspection_date is not in future and
        expiry_date is after inspection_date
        """
        if data['inspection_date'] > timezone.now().date():
            raise serializers.ValidationError(
                "Inspection date cannot be in the future"
            )
        if data['expiry_date'] <= data['inspection_date']:
            raise serializers.ValidationError(
                "Expiry date must be after inspection date"
            )
        return data

class VehicleAvailabilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = VehicleAvailability
        fields = [
            'id', 'start_date', 'end_date',
            'location', 'note', 'created_at'
        ]
        read_only_fields = ['created_at']
    
    def validate(self, data):
        """
        Check that start_date is not in past and
        end_date is after start_date if provided
        """
        if data['start_date'] < timezone.now().date():
            raise serializers.ValidationError(
                "Start date cannot be in the past"
            )
        if data.get('end_date') and data['end_date'] <= data['start_date']:
            raise serializers.ValidationError(
                "End date must be after start date"
            )
        return data

class VehicleSerializer(serializers.ModelSerializer):
    """Full vehicle serializer with all details"""
    owner = UserProfileSerializer(read_only=True)
    documents = VehicleDocumentSerializer(many=True, read_only=True)
    inspections = VehicleInspectionSerializer(many=True, read_only=True)
    availability = VehicleAvailabilitySerializer(many=True, read_only=True)
    verified_by = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = Vehicle
        fields = [
            'id', 'owner', 'body_type', 'loading_type',
            'capacity', 'volume', 'length', 'width',
            'height', 'registration_number',
            'registration_country', 'adr', 'dozvol',
            'tir', 'license_number', 'is_active',
            'is_verified', 'verification_date',
            'verified_by', 'created_at', 'updated_at',
            'documents', 'inspections', 'availability'
        ]
        read_only_fields = [
            'created_at', 'updated_at',
            'is_verified', 'verification_date',
            'verified_by'
        ]

class VehicleListSerializer(serializers.ModelSerializer):
    """Simplified vehicle serializer for list views"""
    owner = UserProfileSerializer(read_only=True)
    documents_count = serializers.IntegerField(
        source='documents.count',
        read_only=True
    )
    documents = VehicleDocumentSerializer(many=True, read_only=True)
    inspections = VehicleInspectionSerializer(many=True, read_only=True)
    availability = VehicleAvailabilitySerializer(many=True, read_only=True)
    verified_by = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = Vehicle
        fields = [
            'id', 'owner', 'body_type', 'loading_type',
            'capacity', 'volume', 'length', 'width',
            'height', 'registration_number',
            'registration_country', 'adr', 'dozvol',
            'tir', 'license_number', 'is_active',
            'is_verified', 'verification_date',
            'verified_by', 'created_at', 'updated_at',
            'documents', 'inspections', 'availability',
            'documents_count', 

            # 'id', 'owner', 'body_type','loading_type',
            # 'capacity', 'registration_number',
            # 'volume', 'length', 'width', 'height',
            # 'is_active', 'is_verified','adr', 'dozvol', 'tir', 'license_number',
            # 'documents_count'
        ]

class VehicleCreateSerializer(serializers.ModelSerializer):
    """Serializer for vehicle creation"""
    class Meta:
        model = Vehicle
        fields = [
            'id',
            'body_type', 'loading_type', 'capacity',
            'volume', 'length', 'width', 'height',
            'registration_number', 'registration_country',
            'adr', 'dozvol', 'tir', 'license_number'
        ]
    
    def create(self, validated_data):
        user = self.context['request'].user
        return Vehicle.objects.create(owner=user, **validated_data)

class VehicleUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating vehicle"""
    class Meta:
        model = Vehicle
        fields = [
            'body_type', 'loading_type', 'capacity',
            'volume', 'length', 'width', 'height',
            'registration_number', 'registration_country',
            'adr', 'dozvol', 'tir', 'license_number',
            'is_active'
        ]

class VehicleVerificationSerializer(serializers.ModelSerializer):
    """Serializer for vehicle verification"""
    class Meta:
        model = Vehicle
        fields = ['is_verified', 'verification_notes']
    
    def update(self, instance, validated_data):
        if validated_data.get('is_verified'):
            validated_data['verification_date'] = timezone.now()
            validated_data['verified_by'] = self.context['request'].user
        return super().update(instance, validated_data)