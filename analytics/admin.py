from django.contrib import admin
from django.urls import path
from django.template.response import TemplateResponse
from django.utils import timezone
from django.db.models import Count

from .models import RecipeViewLog
from recipes.models import Recipe
from account.models import User
from django.contrib.sessions.models import Session
from .views import statistics_data


@admin.register(RecipeViewLog)
class RecipeViewLogAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'user', 'ip_address', 'country', 'timestamp')
    list_filter = ('country', 'recipe')
    search_fields = ('user__email', 'ip_address')


def register_statistics(admin_site):
    def statistics_view(request):
        now = timezone.now()
        week_ago = now - timezone.timedelta(days=7)
        month_ago = now - timezone.timedelta(days=30)

        top_week = (
            Recipe.objects.filter(view_logs__timestamp__gte=week_ago)
            .annotate(total=Count('view_logs'))
            .order_by('-total')[:5]
        )
        top_month = (
            Recipe.objects.filter(view_logs__timestamp__gte=month_ago)
            .annotate(total=Count('view_logs'))
            .order_by('-total')[:5]
        )
        total_views = Recipe.objects.annotate(total=Count('view_logs'))
        user_activity = RecipeViewLog.objects.select_related('user', 'recipe')[:50]

        active_sessions = Session.objects.filter(expire_date__gte=now).count()
        new_users_week = (
            User.objects.filter(recipe_views__timestamp__gte=week_ago)
            .values('id')
            .distinct()
            .count()
        )

        context = dict(
            admin_site.each_context(request),
            top_week=top_week,
            top_month=top_month,
            total_views=total_views,
            user_activity=user_activity,
            active_sessions=active_sessions,
            new_users_week=new_users_week,
        )
        return TemplateResponse(request, 'admin_statistics.html', context)

    original_get_urls = admin_site.get_urls

    def get_urls():
        urls = original_get_urls()
        custom = [
            path('statistics/', admin_site.admin_view(statistics_view), name='statistics'),
            path('statistics/data/', statistics_data, name='statistics-data'),
        ]
        return custom + urls

    admin_site.get_urls = get_urls


register_statistics(admin.site)
