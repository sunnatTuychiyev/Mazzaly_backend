from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Subscription, Author
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
        ('Personal Info', {'fields': ('first_name', 'last_name', 'telegram_id', 'author')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'is_email_verified', 'groups', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'telegram_id', 'author', 'password1', 'password2'),
        }),
    )
    list_display = ('email', 'first_name', 'last_name', 'telegram_id', 'is_staff', 'is_email_verified')
    search_fields = ('email', 'first_name', 'last_name', 'telegram_id')
    ordering = ('email',)
    autocomplete_fields = ('author',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(is_email_verified=True)

admin.site.unregister(Site)
admin.site.register(User, UserAdmin)
admin.site.register(Subscription)
