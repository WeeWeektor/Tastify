import logging

from django.core.exceptions import ObjectDoesNotExist
from django.core.files.uploadedfile import UploadedFile
from django.db import transaction
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError

from profiles.models import CustomerProfile
from shared import get_minio_service, validate_image

logger = logging.getLogger(__name__)


class CustomerProfileService:
    @classmethod
    def create_profile_from_event(cls, event_data: dict) -> CustomerProfile:
        user_id = event_data.get('user_id')
        email = event_data.get('email')

        first_name = event_data.get('first_name', '')
        last_name = event_data.get('last_name', '')

        if first_name or last_name:
            display_name = f'{first_name} {last_name}'.strip()
        else:
            display_name = email.split('@')[0] if email else 'New User'

        profile, created = CustomerProfile.objects.get_or_create(
            user_id=user_id,
            defaults={
                'display_name': display_name,
                'first_name': first_name,
                'last_name': last_name,
                'avatar_url': event_data.get('avatar_url'),
            }
        )

        if created:
            logger.info(f"Created new CustomerProfile for user_id: {user_id}")
        else:
            logger.info(f"CustomerProfile already exists for user_id: {user_id}")

        return profile

    @classmethod
    @transaction.atomic
    def update_profile(cls, user_id: str, validated_data: dict, avatar_file: UploadedFile = None) -> CustomerProfile:
        try:
            profile = CustomerProfile.objects.select_for_update().get(user_id=user_id)
        except ObjectDoesNotExist:
            raise ValidationError({"detail": _("Customer profile does not exist.")})

        if avatar_file:
            validate_image(avatar_file)

            try:
                minio_service = get_minio_service()
                file_url = minio_service.upload_file(
                    file_obj=avatar_file,
                    bucket_name='customer-avatars',
                    folder=f"users/{user_id}"
                )
                validated_data['avatar_url'] = file_url
            except Exception as e:
                logger.error(f"Failed to upload avatar image for user_id {user_id} to MinIO: {e}")
                raise ValidationError({"avatar": _("Failed to upload avatar image. Please try again later.")})

        for attr, value in validated_data.items():
            setattr(profile, attr, value)

        profile.save()
        logger.info(f"Updated CustomerProfile successfully for user_id: {user_id}")

        return profile
