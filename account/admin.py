from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    User, Subscription, Author, TelegramLinkToken, EmailOTPTelegramLink, 
    TelegramLinkNonce, AuthAuditLog
)
from django.contrib.sites.models import Site

class SubscriptionInline(admin.TabularInline):
    model = Subscription
    extra = 0

@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    search_fields = ('name',)
    list_display = ('name',)


class UserAdmin(BaseUserAdmin):
    inlines = [SubscriptionInline]
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {
            'fields': ('first_name', 'last_name', 'author')
        }),
        ('Telegram Info', {
            'fields': ('telegram_id', 'telegram_username', 'telegram_first_name', 'telegram_last_name', 'telegram_photo_url'),
            'classes': ('collapse',)
        }),
        ('Auth Info', {
            'fields': ('login_method', 'created_via', 'telegram_linked_at', 'last_login_at'),
            'classes': ('collapse',)
        }),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'is_email_verified', 'groups', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'telegram_id', 'author', 'password1', 'password2'),
        }),
    )
    list_display = ('email', 'first_name', 'last_name', 'telegram_id', 'login_method', 'is_staff', 'is_email_verified', 'last_login_at')
    search_fields = ('email', 'first_name', 'last_name', 'telegram_id', 'telegram_username')
    ordering = ('-last_login_at', 'email')
    autocomplete_fields = ('author',)
    list_filter = ('login_method', 'created_via', 'is_staff', 'is_email_verified', 'is_active')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Remove filter to show all users
        return qs

@admin.register(TelegramLinkToken)
class TelegramLinkTokenAdmin(admin.ModelAdmin):
    list_display = ('token', 'user', 'created_at', 'expires_at', 'used_at', 'is_valid')
    list_filter = ('used_at', 'expires_at', 'created_at')
    search_fields = ('token', 'user__email', 'user__telegram_id')
    readonly_fields = ('token', 'created_at', 'used_at')
    date_hierarchy = 'created_at'
    
    def is_valid(self, obj):
        return obj.is_valid
    is_valid.boolean = True
    is_valid.short_description = 'Valid'


@admin.register(EmailOTPTelegramLink)
class EmailOTPTelegramLinkAdmin(admin.ModelAdmin):
    list_display = ('email', 'telegram_id', 'user', 'created_at', 'expires_at', 'attempts', 'is_verified', 'is_valid')
    list_filter = ('verified_at', 'expires_at', 'created_at')
    search_fields = ('email', 'telegram_id', 'user__email')
    readonly_fields = ('code_hash', 'password', 'created_at', 'verified_at')
    date_hierarchy = 'created_at'
    
    def is_verified(self, obj):
        return obj.is_verified
    is_verified.boolean = True
    is_verified.short_description = 'Verified'
    
    def is_valid(self, obj):
        return obj.is_valid
    is_valid.boolean = True
    is_valid.short_description = 'Valid'


@admin.register(TelegramLinkNonce)
class TelegramLinkNonceAdmin(admin.ModelAdmin):
    list_display = ('nonce', 'user', 'created_at', 'expires_at', 'used', 'used_at', 'telegram_user_id', 'is_valid')
    list_filter = ('used', 'expires_at', 'created_at')
    search_fields = ('user__email', 'nonce', 'telegram_user_id')
    readonly_fields = ('nonce', 'created_at', 'used_at')
    date_hierarchy = 'created_at'
    
    def is_valid(self, obj):
        return obj.is_valid
    is_valid.boolean = True
    is_valid.short_description = 'Valid'


@admin.register(AuthAuditLog)
class AuthAuditLogAdmin(admin.ModelAdmin):
    list_display = ('action', 'platform', 'user', 'success', 'created_at', 'ip_address')
    list_filter = ('action', 'platform', 'success', 'created_at')
    search_fields = ('user__email', 'telegram_id', 'email', 'ip_address')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)


admin.site.unregister(Site)
admin.site.register(User, UserAdmin)
admin.site.register(Subscription)
