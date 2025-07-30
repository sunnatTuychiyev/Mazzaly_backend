from django.http import HttpRequest


def get_client_ip(request: HttpRequest) -> str:
    """Return the real client IP address.

    Checks ``X-Forwarded-For`` first in case the app is behind a proxy.
    """
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    if xff:
        # X-Forwarded-For may contain multiple addresses, take the first
        ip = xff.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip or ''
