def mark_social_user_verified(backend, user, response, *args, **kwargs):
    """
        Кастомний крок пайплайну. Активує юзера та ініціює
        створення профілю в іншому сервісі.
    """

    if backend.name == 'google-oauth2':
        fields_to_update = []

        if not user.is_verified:
            user.is_verified = True
            fields_to_update.append('is_verified')

        if not user.is_active:
            user.is_active = True
            fields_to_update.append('is_active')

        if not getattr(user, 'role', None):
            user.role = 'customer'
            fields_to_update.append('role')

        if fields_to_update:
            user.save(update_fields=fields_to_update)

        # TODO
        # google_avatar_url = response.get('picture')
        #
        # # Генеруємо подію для іншого сервісу.
        # # Оскільки в транзакції, найкраще викликати асинхронну таску Celery,
        # # яка відправить подію в Kafka після успішного коміту в БД.
        # from authentication.tasks import send_user_created_event
        #
        # # Передаємо id, роль та аватарку, щоб сервіс профілів знав, який профіль створити
        # send_user_created_event.delay(
        #     user_id=str(user.id),
        #     email=user.email,
        #     role=user.role,
        #     avatar_url=google_avatar_url
        # )
