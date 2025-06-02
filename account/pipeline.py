from django.contrib.auth import get_user_model

def create_user(strategy, details, backend, user=None, *args, **kwargs):
    if user:
        return {'is_new': False, 'user': user}
    
    User = get_user_model()
    email = details.get('email')
    if not email:
        return None
    
    user = User.objects.create_user(
        email=email,
        first_name=details.get('first_name', ''),
        last_name=details.get('last_name', ''),
        password=None
    )
    return {'is_new': True, 'user': user}
