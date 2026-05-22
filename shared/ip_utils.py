def get_client_ip(request) -> str | None:
    """
    Отримує реальну IP адресу клієнта, враховуючи Reverse Proxy (Nginx).
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
