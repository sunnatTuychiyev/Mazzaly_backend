from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Subscription
from django.contrib.sites.models import Site

class SubscriptionInline(admin.TabularInline):
    model = Subscription
    extra = 0

class UserAdmin(BaseUserAdmin):
    inlines = [SubscriptionInline]
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'telegram_id')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'telegram_id', 'password1', 'password2'),
        }),
    )
    list_display = ('email', 'first_name', 'last_name', 'telegram_id', 'is_staff')
    search_fields = ('email', 'first_name', 'last_name', 'telegram_id')
    ordering = ('email',)

admin.site.unregister(Site)
admin.site.register(User, UserAdmin)
admin.site.register(Subscription)
