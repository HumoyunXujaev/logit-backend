from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType
from .models import (
    Notification, Favorite, Rating, TelegramGroup,
    TelegramMessage, SearchFilter
)
from users.serializers import UserProfileSerializer

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            'id', 'type', 'message', 'is_read',
            'created_at', 'content_type', 'object_id'
        ]
        read_only_fields = ['created_at']

class FavoriteSerializer(serializers.ModelSerializer):
    content_type = serializers.SlugRelatedField(
        queryset=ContentType.objects.all(),
        slug_field='model'
    )
    
    class Meta:
        model = Favorite
        fields = [
            'id', 'content_type', 'object_id',
            'created_at'
        ]
        read_only_fields = ['created_at']
    
    def validate(self, data):
        """
        Validate that the object exists
        """
        try:
            content_type = data['content_type']
            model_class = content_type.model_class()
            model_class.objects.get(id=data['object_id'])
        except Exception:
            raise serializers.ValidationError(
                "Invalid object_id for the given content_type"
            )
        return data

class RatingSerializer(serializers.ModelSerializer):
    from_user = UserProfileSerializer(read_only=True)
    to_user = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = Rating
        fields = [
            'id', 'from_user', 'to_user', 'score',
            'comment', 'created_at'
        ]
        read_only_fields = ['created_at']

class RatingCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rating
        fields = ['to_user', 'score', 'comment']
    
    def validate_to_user(self, value):
        """
        Validate that users can't rate themselves
        """
        if value == self.context['request'].user:
            raise serializers.ValidationError(
                "You cannot rate yourself"
            )
        return value
    
    def create(self, validated_data):
        from_user = self.context['request'].user
        return Rating.objects.create(from_user=from_user, **validated_data)

class TelegramGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = TelegramGroup
        fields = [
            'id', 'telegram_id', 'name', 'description',
            'is_active', 'last_sync', 'created_at'
        ]
        read_only_fields = ['last_sync', 'created_at']

class TelegramMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = TelegramMessage
        fields = [
            'id', 'telegram_id', 'group', 'message_text',
            'processed', 'processed_at', 'created_at', 'cargo'
        ]
        read_only_fields = [
            'processed', 'processed_at', 'created_at', 'cargo'
        ]

class SearchFilterSerializer(serializers.ModelSerializer):
    class Meta:
        model = SearchFilter
        fields = [
            'id', 'name', 'filter_data',
            'notifications_enabled', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def create(self, validated_data):
        user = self.context['request'].user
        return SearchFilter.objects.create(user=user, **validated_data)

class SearchFilterUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SearchFilter
        fields = ['name', 'filter_data', 'notifications_enabled']