from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

class UserManager(BaseUserManager):
    def create_user(self, email, first_name, last_name, password=None):
        if not email:
            raise ValueError('Email required')
        email = self.normalize_email(email)
        user = self.model(email=email, first_name=first_name, last_name=last_name)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, first_name, last_name, password):
        user = self.create_user(email, first_name, last_name, password)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user

class User(AbstractBaseUser, PermissionsMixin):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    telegram_id = models.CharField(max_length=64, unique=True, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_email_verified = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    def __str__(self):
        return self.email

    @property
    def current_plan(self):
        return get_user_current_plan(self)


class EmailOTP(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='email_otp')
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"OTP for {self.user.email}"


class Subscription(models.Model):
    PLAN_STANDARD = 'standard'
    PLAN_HEALTHY = 'healthy'
    PLAN_PREMIUM = 'premium'

    PLAN_CHOICES = [
        (PLAN_STANDARD, 'Standard'),
        (PLAN_HEALTHY, 'Healthy'),
        (PLAN_PREMIUM, 'Premium'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='subscriptions')
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES)
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
        return f"{self.user.email} - {self.plan}"


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
