from django.contrib import admin
from django.urls import path
from django.template.response import TemplateResponse
from django.utils import timezone
from django.db.models import Count
from django.core.paginator import Paginator

from .models import RecipeViewLog, SiteVisit
from recipes.models import Recipe
from account.models import User
from django.contrib.sessions.models import Session
from .views import statistics_data, monthly_report_pdf


@admin.register(RecipeViewLog)
class RecipeViewLogAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'user', 'ip_address', 'country', 'timestamp')
    list_filter = ('country', 'recipe')
    search_fields = ('user__email', 'ip_address')


@admin.register(SiteVisit)
class SiteVisitAdmin(admin.ModelAdmin):
    list_display = ('ip_address', 'timestamp')


def register_statistics(admin_site):
    """Attach statistics views to the given ``AdminSite`` instance."""
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
        total_views_qs = Recipe.objects.annotate(total=Count('view_logs')).order_by('-total')
        views_paginator = Paginator(total_views_qs, 20)
        views_page = views_paginator.get_page(request.GET.get('views_page'))

        user_activity_qs = RecipeViewLog.objects.select_related('user', 'recipe').order_by('-timestamp')
        activity_paginator = Paginator(user_activity_qs, 20)
        activity_page = activity_paginator.get_page(request.GET.get('activity_page'))

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
            total_views_page=views_page,
            total_views_paginator=views_paginator,
            user_activity_page=activity_page,
            user_activity_paginator=activity_paginator,
            active_sessions=active_sessions,
            new_users_week=new_users_week,
        )
        return TemplateResponse(request, 'admin_statistics.html', context)

    # Preserve the original ``get_urls`` so we can call it without recursion
    original_get_urls = admin_site.get_urls

    def get_urls():
        """Return the default admin URLs plus the custom statistics routes."""
        custom = [
            path('statistics/', admin_site.admin_view(statistics_view), name='statistics'),
            path('statistics/data/', admin_site.admin_view(statistics_data), name='statistics-data'),
            path('statistics/report/', admin_site.admin_view(monthly_report_pdf), name='statistics-report'),
        ]
        urls = original_get_urls()
        return custom + urls

    admin_site.get_urls = get_urls


register_statistics(admin.site)
