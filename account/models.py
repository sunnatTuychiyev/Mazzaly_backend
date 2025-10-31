from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

# Subscription plan constants shared between User and Subscription models
SUB_PLAN_STANDARD = 'standard'
SUB_PLAN_HEALTHY = 'healthy'
SUB_PLAN_PREMIUM = 'premium'

SUB_PLAN_CHOICES = [
    (SUB_PLAN_STANDARD, 'Standard'),
    (SUB_PLAN_HEALTHY, 'Healthy'),
    (SUB_PLAN_PREMIUM, 'Premium'),
]

class UserManager(BaseUserManager):
    def create_user(self, email, first_name, last_name, password=None, **extra_fields):
        if not email:
            raise ValueError('Email required')
        email = self.normalize_email(email)
        user = self.model(email=email, first_name=first_name, last_name=last_name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, first_name, last_name, password):
        user = self.create_user(email, first_name, last_name, password)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user

class Author(models.Model):
    name = models.CharField(max_length=255, unique=True)
    bio = models.TextField(blank=True)

    def __str__(self):
        return self.name


class User(AbstractBaseUser, PermissionsMixin):
    # Core fields (existing)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)  # Placeholder emails for telegram-only users
    telegram_id = models.CharField(max_length=64, unique=True, null=True, blank=True)
    author = models.ForeignKey('Author', on_delete=models.SET_NULL, null=True, blank=True, related_name='users')
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_email_verified = models.BooleanField(default=False)
    
    # New unified auth fields (all nullable, additive only)
    telegram_username = models.CharField(max_length=255, null=True, blank=True)
    telegram_first_name = models.CharField(max_length=255, null=True, blank=True)
    telegram_last_name = models.CharField(max_length=255, null=True, blank=True)
    telegram_photo_url = models.URLField(max_length=500, null=True, blank=True)
    
    LOGIN_METHOD_EMAIL = 'email'
    LOGIN_METHOD_TELEGRAM = 'telegram'
    LOGIN_METHOD_BOTH = 'both'
    LOGIN_METHOD_CHOICES = [
        (LOGIN_METHOD_EMAIL, 'Email'),
        (LOGIN_METHOD_TELEGRAM, 'Telegram'),
        (LOGIN_METHOD_BOTH, 'Both'),
    ]
    login_method = models.CharField(
        max_length=20,
        choices=LOGIN_METHOD_CHOICES,
        default=LOGIN_METHOD_EMAIL,
        null=True,
        blank=True
    )
    
    CREATED_VIA_WEB = 'web'
    CREATED_VIA_TELEGRAM = 'telegram'
    CREATED_VIA_CHOICES = [
        (CREATED_VIA_WEB, 'Web'),
        (CREATED_VIA_TELEGRAM, 'Telegram'),
    ]
    created_via = models.CharField(
        max_length=20,
        choices=CREATED_VIA_CHOICES,
        default=CREATED_VIA_WEB,
        null=True,
        blank=True
    )
    
    telegram_linked_at = models.DateTimeField(null=True, blank=True)
    last_login_at = models.DateTimeField(null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        indexes = [
            models.Index(fields=['telegram_id']),
            models.Index(fields=['login_method']),
            models.Index(fields=['email']),
        ]

    def __str__(self):
        if self.email:
            return self.email
        elif self.telegram_id:
            return f"Telegram:{self.telegram_id}"
        else:
            return f"User:{self.id}"

    @property
    def current_plan(self):
        return get_user_current_plan(self)
    
    def get_login_method(self):
        """Automatically determine login method based on user data"""
        # Check if email is a real email (not a placeholder)
        has_email = bool(
            self.email and 
            not self.email.startswith('tg_') and 
            '@telegram.local' not in self.email and
            '@example.com' not in self.email
        )
        has_telegram = bool(self.telegram_id)
        
        if has_email and has_telegram:
            return self.LOGIN_METHOD_BOTH
        elif has_telegram:
            return self.LOGIN_METHOD_TELEGRAM
        else:
            return self.LOGIN_METHOD_EMAIL


class EmailOTP(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='email_otp')
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        user_id = self.user.email or f"Telegram:{self.user.telegram_id}" or f"User:{self.user.id}"
        return f"OTP for {user_id}"


class TelegramLinkToken(models.Model):
    """One-time token for linking Telegram account to web user account."""
    token = models.CharField(max_length=64, unique=True, db_index=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='telegram_link_tokens')
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    client_ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['token', 'used_at']),
            models.Index(fields=['expires_at', 'used_at']),
        ]

    def __str__(self):
        user_id = self.user.email or f"Telegram:{self.user.telegram_id}" or f"User:{self.user.id}"
        return f"Token {self.token[:8]}... for {user_id}"

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at

    @property
    def is_used(self):
        return self.used_at is not None

    @property
    def is_valid(self):
        return not self.is_expired and not self.is_used


class EmailOTPTelegramLink(models.Model):
    """OTP for linking email to Telegram account during Mini App registration."""
    email = models.EmailField()
    code = models.CharField(max_length=6)
    telegram_id = models.CharField(max_length=64, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    attempts = models.IntegerField(default=0)
    verified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email', 'telegram_id']),
            models.Index(fields=['telegram_id', 'expires_at']),
        ]

    def __str__(self):
        return f"OTP for {self.email} (Telegram: {self.telegram_id})"

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at

    @property
    def is_verified(self):
        return self.verified_at is not None

    @property
    def is_valid(self):
        return not self.is_expired and not self.is_verified and self.attempts < 5


class AuthAuditLog(models.Model):
    """Audit log for all authentication actions"""
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='auth_logs')
    action = models.CharField(max_length=50)  # login, logout, link_telegram, link_email, etc.
    platform = models.CharField(max_length=20)  # web, telegram
    telegram_id = models.CharField(max_length=64, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user_id']),
            models.Index(fields=['created_at']),
            models.Index(fields=['action', 'platform']),
        ]

    def __str__(self):
        return f"{self.action} - {self.platform} - {self.user_id if self.user else 'No user'}"


class Subscription(models.Model):
    PLAN_STANDARD = SUB_PLAN_STANDARD
    PLAN_HEALTHY = SUB_PLAN_HEALTHY
    PLAN_PREMIUM = SUB_PLAN_PREMIUM

    PLAN_CHOICES = SUB_PLAN_CHOICES

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='subscriptions')
    plan = models.CharField(max_length=20, choices=SUB_PLAN_CHOICES)
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.plan != self.PLAN_STANDARD and not self.end_date:
            self.end_date = self.start_date + timedelta(days=30)
        super().save(*args, **kwargs)

    @property
    def is_active(self):
        return (
            self.start_date <= timezone.now()
            and (self.end_date is None or self.end_date >= timezone.now())
        )

    def __str__(self):
        user_identifier = self.user.email or f"Telegram:{self.user.telegram_id}" or f"User:{self.user.id}"
        return f"{user_identifier} - {self.plan}"


def get_user_current_plan(user):
    now = timezone.now()
    active = (
        user.subscriptions
        .filter(start_date__lte=now)
        .filter(models.Q(end_date__isnull=True) | models.Q(end_date__gte=now))
        .order_by('-start_date')
        .first()
    )
    if active:
        return active.plan
    return Subscription.PLAN_STANDARD
