from django.conf import settings
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import generics, permissions, status
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response

from shared import BaseRedisService
from shared.decorators import cache_user_data, invalidate_user_data_cache
from .models import CustomerProfile
from .serializers import CustomerProfileSerializer
from .services import CustomerProfileService

profile_cache = BaseRedisService(
    redis_url=settings.REDIS_URL,
    prefix="user_profile",
    ttl_seconds=3600
)


@extend_schema_view(
    get=extend_schema(
        summary="Отримання профілю користувача",
        description="Повертає профіль поточного авторизованого користувача. Ідентифікація відбувається автоматично за допомогою JWT токена.",
        tags=['Customer Profile'],
        request=None,
    ),
    put=extend_schema(
        summary="Повне оновлення профілю",
        description="Оновлює всі дані профілю користувача. Підтримує формат `multipart/form-data` для завантаження нового файлу `avatar`.",
        tags=['Customer Profile'],
        request=CustomerProfileSerializer,
    ),
    patch=extend_schema(
        summary="Часткове оновлення профілю",
        description="Оновлює окремі поля профілю (можна передати лише ті поля, які змінилися). Підтримує завантаження файлу `avatar`.",
        tags=['Customer Profile'],
        request=CustomerProfileSerializer,
    )
)
class CustomerProfileView(generics.RetrieveUpdateAPIView):
    """
        Ендпоінт для отримання (GET) та оновлення (PATCH/PUT) профілю
        поточного автентифікованого користувача.
    """
    serializer_class = CustomerProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_object(self):
        """
            Перевизначення методу для отримання об'єкта.
            Беремо ID прямо з JWT токена.
            Це гарантує, що юзер ніколи не зможе отримати або змінити чужий профіль.
        """
        return get_object_or_404(CustomerProfile, user_id=self.request.user.id)

    @cache_user_data(redis_client=profile_cache)
    def retrieve(self, request, *args, **kwargs):
        """
            Перевизначений стандартний метод GET, щоб викликати декоратор кешування.
            Уся логіка прихована в декораторі.
        """
        return super().retrieve(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        profile = self.get_object()

        serializer = self.get_serializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        avatar_file = request.FILES.get('avatar')

        updated_profile = CustomerProfileService.update_profile(
            user_id=request.user.id,
            validated_data=serializer.validated_data,
            avatar_file=avatar_file,
        )

        result_serializer = self.get_serializer(updated_profile)

        invalidate_user_data_cache(redis_client=profile_cache, user_id=str(request.user.id))

        return Response(result_serializer.data, status=status.HTTP_200_OK)
