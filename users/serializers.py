from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import UserDocument
from drf_spectacular.utils import extend_schema_field
from django.utils import timezone
from datetime import datetime
import pytz

User = get_user_model()

# Create a minimal UserProfile serializer for UserDocument
class BasicUserProfileSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    
    class Meta:
        model = User
        fields = ['telegram_id', 'username', 'full_name']

class UserDocumentSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()
    verified_by = BasicUserProfileSerializer(read_only=True)

    class Meta:
        model = UserDocument
        fields = [
            'id', 'type', 'title', 'file', 'file_url',
            'uploaded_at', 'verified', 'verified_at',
            'verified_by', 'notes'
        ]
        read_only_fields = ['uploaded_at', 'verified', 'verified_at', 'verified_by']
    
    def get_file_url(self, obj):
        if obj.file:
            request = self.context.get('request')
            if request is not None:
                return request.build_absolute_uri(obj.file.url)
        return None
    
# class UserDocumentSerializer(serializers.ModelSerializer):

#     file_url = serializers.SerializerMethodField()
#     verified_by = UserProfileSerializer(read_only=True)

#     class Meta:
#         model = UserDocument
#         fields = [
#             'id', 'type', 'title', 'file', 'file_url',
#             'uploaded_at', 'verified', 'verified_at',
#             'verified_by', 'notes'
#         ]
#         read_only_fields = ['uploaded_at', 'verified', 'verified_at', 'verified_by']
    
#     def get_file_url(self, obj):
#         if obj.file:
#             request = self.context.get('request')
#             if request is not None:
#                 return request.build_absolute_uri(obj.file.url)
#         return None
    
class TelegramAuthSerializer(serializers.Serializer):
    hash = serializers.CharField(required=True)
    user = serializers.JSONField(required=True)
    auth_date = serializers.IntegerField(required=True)

    def validate_auth_date(self, value):
        """Validate that auth_date is not too old"""
        # Convert timestamp to timezone-aware datetime
        auth_timestamp = datetime.fromtimestamp(value, tz=pytz.UTC)
        now = timezone.now()
        
        # Calculate time difference
        time_difference = now - auth_timestamp
        
        # Check if auth_date is not older than 1 day
        if time_difference.days > 1:
            raise serializers.ValidationError(
                "Authentication data has expired"
            )
        return value

class UserProfileSerializer(serializers.ModelSerializer):
    documents = UserDocumentSerializer(many=True, read_only=True)
    rating_count = serializers.SerializerMethodField()
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    
    class Meta:
        model = User
        fields = [
            'telegram_id', 'username', 'full_name', 'type', 'role',
            'preferred_language', 'phone_number', 'whatsapp_number',
            'company_name', 'position', 'student_id', 'group_name',
            'study_language', 'curator_name', 'end_date', 'rating',
            'rating_count', 'is_verified', 'verification_date',
            'documents', 'date_joined', 'last_login', 'tariff'
        ]
        read_only_fields = [
            'telegram_id', 'rating', 'is_verified',
            'verification_date', 'date_joined', 'last_login'
        ]
    
    @extend_schema_field({'type': 'integer'})
    def get_rating_count(self, obj) -> int:
        return obj.ratings_received.count()
    
    # def get_rating_count(self, obj):
    #     return obj.ratings_received.count()


    
    
class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'phone_number', 'whatsapp_number', 'preferred_language',
            'company_name', 'position', 'type', 'role',
            'student_id', 'group_name', 'study_language',
            'curator_name', 'end_date', 'tariff'
        ]
    
    def validate(self, data):
        """
        Validate based on user type and role
        """
        user_type = data.get('type')
        user_role = data.get('role')
        
        if user_type == 'legal':
            if not data.get('company_name'):
                raise serializers.ValidationError({
                    "company_name": "Company name is required for legal entities"
                })
                
        if user_role == 'student':
            required_fields = ['student_id', 'group_name', 'study_language']
            missing_fields = [
                field for field in required_fields 
                if not data.get(field)
            ]
            if missing_fields:
                raise serializers.ValidationError({
                    field: "This field is required for students"
                    for field in missing_fields
                })
                
        if user_role in ['carrier', 'transport-company']:
            if not data.get('phone_number'):
                raise serializers.ValidationError({
                    "phone_number": "Phone number is required for carriers"
                })
                
        return data

class UserDocumentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserDocument
        fields = ['type', 'title', 'file']
    
    def validate(self, data):
        """
        Validate document type based on user role
        """
        user = self.context['request'].user
        doc_type = data.get('type')
        
        if user.role == 'carrier' and doc_type != 'driver_license':
            raise serializers.ValidationError(
                "Carriers can only upload driver licenses"
            )
            
        if user.role == 'student' and doc_type != 'passport':
            raise serializers.ValidationError(
                "Students can only upload passports"
            )
            
        return data

class UserVerificationSerializer(serializers.Serializer):
    is_verified = serializers.BooleanField(required=True)
    notes = serializers.CharField(required=False, allow_blank=True)
    
    def update(self, instance, validated_data):
        instance.is_verified = validated_data['is_verified']
        if validated_data.get('notes'):
            instance.verification_notes = validated_data['notes']
        if validated_data['is_verified']:
            instance.verification_date = timezone.now()
        instance.save()
        return instance