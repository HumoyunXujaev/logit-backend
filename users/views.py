from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import transaction
from drf_spectacular.utils import extend_schema, OpenApiParameter
from .serializers import (
    UserProfileSerializer,
    TelegramAuthSerializer,
    UserUpdateSerializer,
    UserDocumentSerializer,
    UserDocumentCreateSerializer,
    UserVerificationSerializer
)
from .models import UserDocument
from .auth import TelegramAuthBackend
from core.permissions import IsStaffOrReadOnly

User = get_user_model()

class UserViewSet(viewsets.GenericViewSet):
    queryset = User.objects.all()
    serializer_class = UserProfileSerializer
    telegram_backend = TelegramAuthBackend()
    
    def get_permissions(self):
        if self.action == 'telegram_auth':
            permission_classes = [permissions.AllowAny]
        elif self.action == 'register':
            permission_classes = [permissions.AllowAny]
        elif self.action in ['verify_user', 'verify_document']:
            permission_classes = [permissions.IsAdminUser]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny])
    def register(self, request):
        """
        Register new user with both Telegram and profile data
        """
        try:
            with transaction.atomic():
                # Валидируем telegram данные
                telegram_serializer = TelegramAuthSerializer(data=request.data)
                telegram_serializer.is_valid(raise_exception=True)
                
                telegram_data = telegram_serializer.validated_data
                telegram_user = telegram_data['user']
                telegram_id = str(telegram_user['id'])
                
                # Проверяем существование пользователя
                if User.objects.filter(telegram_id=telegram_id).exists():
                    return Response(
                        {'detail': 'User already exists'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                # Получаем дополнительные данные пользователя
                user_data = request.data.get('userData', {})
                print(user_data)
                print(telegram_user)
                print(telegram_data)
                # Создаем пользователя с базовыми и дополнительными данными
                user = User.objects.create(
                    telegram_id=telegram_id,
                    username=telegram_user.get('username', ''),
                    first_name=telegram_user.get('first_name', ''),
                    last_name=telegram_user.get('last_name', ''),
                    language_code=telegram_user.get('language_code', 'ru'),
                    is_active=True,
                    type=user_data.get('type'),
                    role=user_data.get('role'),
                    tariff=user_data.get('tariff'),
                    preferred_language=user_data.get('preferred_language'),
                    phone_number=user_data.get('phoneNumber'),
                    whatsapp_number=user_data.get('whatsappNumber'),
                    company_name=user_data.get('companyName'),
                    position=user_data.get('position'),
                    registration_certificate=user_data.get('registrationCertificate'),
                    student_id=user_data.get('studentId'),
                    group_name=user_data.get('groupName'),
                    study_language=user_data.get('studyLanguage'),
                    curator_name=user_data.get('curatorName'),
                    end_date=user_data.get('endDate'),
                    is_verified=False,
                    date_joined=timezone.now(),
                    last_login=timezone.now()
                    # Добавьте другие поля из user_data
                )

                # Генерируем токены
                refresh = RefreshToken.for_user(user)
                refresh.set_exp(lifetime=timezone.timedelta(days=365))
                
                return Response({
                    'access': str(refresh.access_token),
                    'refresh': str(refresh),
                    'user': UserProfileSerializer(user).data
                }, status=status.HTTP_201_CREATED)
                
        except Exception as e:
            print(e)
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


    @extend_schema(
        description='Authenticate using Telegram WebApp data',
        request=TelegramAuthSerializer,
        responses={200: {'description': 'Returns JWT tokens if authentication successful'}}
    )
    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny])
    def telegram_auth(self, request):
        """
        Authenticate user through Telegram
        """
        try:
            serializer = TelegramAuthSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            telegram_data = serializer.validated_data
            telegram_id = str(telegram_data['user']['id'])
            
            # Try to find existing user
            try:
                user = User.objects.get(telegram_id=telegram_id)
            except User.DoesNotExist:
                # Return 404 to trigger registration flow
                return Response(
                    {'detail': 'User not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Update last login for existing user
            user.last_login = timezone.now()
            user.save(update_fields=['last_login'])
            
            # Generate tokens
            refresh = RefreshToken.for_user(user)
            refresh.set_exp(lifetime=timezone.timedelta(days=365))
            
            return Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': UserProfileSerializer(user).data
            })
            
        except Exception as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @extend_schema(
        description='Get current user profile',
        responses={200: UserProfileSerializer}
    )
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user's profile"""
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)

    @extend_schema(
        description='Update current user profile',
        request=UserUpdateSerializer,
        responses={200: UserProfileSerializer}
    )
    @action(detail=False, methods=['put','patch'], permission_classes=[permissions.IsAuthenticated])
    def update_profile(self, request):
        """
        Update user profile
        """
        try:
            user = request.user
            serializer = UserUpdateSerializer(user, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            user = serializer.save()
            
            return Response(UserProfileSerializer(user).data)
        except Exception as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @extend_schema(
        description='Upload user document',
        request=UserDocumentCreateSerializer,
        responses={201: UserDocumentSerializer}
    )
    @action(detail=False, methods=['post'])
    def upload_document(self, request):
        """Upload a user document"""
        serializer = UserDocumentCreateSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        document = serializer.save(user=request.user)
        
        return Response(
            UserDocumentSerializer(document).data,
            status=status.HTTP_201_CREATED
        )

    @extend_schema(
        description='Get user documents',
        responses={200: UserDocumentSerializer(many=True)}
    )
    @action(detail=False, methods=['get'])
    def documents(self, request):
        """Get current user's documents"""
        documents = UserDocument.objects.filter(user=request.user)
        serializer = UserDocumentSerializer(documents, many=True)
        return Response(serializer.data)

    @extend_schema(
        description='Verify user',
        request=UserVerificationSerializer,
        responses={200: UserProfileSerializer}
    )
    @action(detail=True, methods=['post'])
    def verify_user(self, request, pk=None):
        """Verify a user (admin only)"""
        user = self.get_object()
        serializer = UserVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        updated_user = serializer.update(user, serializer.validated_data)
        
        return Response(UserProfileSerializer(updated_user).data)

    @extend_schema(
        description='Verify document',
        responses={200: UserDocumentSerializer}
    )
    @action(detail=False, methods=['post'], url_path='documents/(?P<document_id>[^/.]+)/verify')
    def verify_document(self, request, document_id=None):
        """Verify a user document (admin only)"""
        document = UserDocument.objects.get(id=document_id)
        document.verified = True
        document.verified_at = timezone.now()
        document.verified_by = request.user
        document.save()
        
        return Response(UserDocumentSerializer(document).data)

    @extend_schema(
        description='Logout current user',
        responses={200: {'description': 'User logged out successfully'}}
    )
    @action(detail=False, methods=['post'])
    def logout(self, request):
        """Logout current user"""
        try:
            refresh_token = request.data.get('refresh')
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({'detail': 'Successfully logged out'})
        except Exception:
            return Response(
                {'detail': 'Invalid token'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context