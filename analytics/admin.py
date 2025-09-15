from django.contrib import admin
from django.urls import path
from django.template.response import TemplateResponse
from django.http import JsonResponse, HttpResponse
import csv
from django.utils import timezone
from django.db.models import Count, Q
from django.core.paginator import Paginator

from .models import RecipeViewLog
from recipes.models import Recipe, RecipeSubmission
from account.models import User, Author
from django.contrib.sessions.models import Session
from .views import statistics_data, monthly_report_pdf


@admin.register(RecipeViewLog)
class RecipeViewLogAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'user', 'ip_address', 'country', 'timestamp')
    list_filter = ('country', 'recipe')
    search_fields = ('user__email', 'ip_address')


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
            path('statistics/authors/', admin_site.admin_view(author_statistics_view), name='author-statistics'),
            path('statistics/authors/data/', admin_site.admin_view(author_statistics_data), name='author-statistics-data'),
            path('statistics/authors/export/', admin_site.admin_view(author_statistics_export), name='author-statistics-export'),
        ]
        urls = original_get_urls()
        return custom + urls

    admin_site.get_urls = get_urls


register_statistics(admin.site)


def author_statistics_view(request):
    now = timezone.now()
    week_ago = now - timezone.timedelta(days=7)
    month_ago = now - timezone.timedelta(days=30)

    authors_qs = (
        Author.objects.all()
        .annotate(
            total_submissions=Count('recipe_submissions', distinct=True),
            approved_submissions=Count(
                'recipe_submissions',
                filter=Q(recipe_submissions__status=RecipeSubmission.STATUS_APPROVED),
                distinct=True,
            ),
            rejected_submissions=Count(
                'recipe_submissions',
                filter=Q(recipe_submissions__status=RecipeSubmission.STATUS_REJECTED),
                distinct=True,
            ),
            pending_submissions=Count(
                'recipe_submissions',
                filter=Q(recipe_submissions__status=RecipeSubmission.STATUS_PENDING),
                distinct=True,
            ),
            total_recipes=Count('recipes', distinct=True),
            recipes_30d=Count('recipes', filter=Q(recipes__created_at__gte=month_ago), distinct=True),
            recipes_7d=Count('recipes', filter=Q(recipes__created_at__gte=week_ago), distinct=True),
        )
        .order_by('-total_recipes', '-approved_submissions', 'name')
    )

    paginator = Paginator(authors_qs, 25)
    page = paginator.get_page(request.GET.get('page'))

    total_authors = Author.objects.count()
    total_submissions = RecipeSubmission.objects.count()
    total_approved = RecipeSubmission.objects.filter(status=RecipeSubmission.STATUS_APPROVED).count()
    total_rejected = RecipeSubmission.objects.filter(status=RecipeSubmission.STATUS_REJECTED).count()
    total_recipes = Recipe.objects.exclude(author__isnull=True).count()

    top_author = (
        Author.objects
        .annotate(total_recipes=Count('recipes'))
        .order_by('-total_recipes')
        .first()
    )

    context = dict(
        admin.site.each_context(request),
        title='Author statistics',
        page=page,
        paginator=paginator,
        total_authors=total_authors,
        total_submissions=total_submissions,
        total_approved=total_approved,
        total_rejected=total_rejected,
        total_recipes=total_recipes,
        top_author=top_author,
    )

    return TemplateResponse(request, 'admin_author_statistics.html', context)


def _author_base_queryset(now):
    week_ago = now - timezone.timedelta(days=7)
    month_ago = now - timezone.timedelta(days=30)
    return (
        Author.objects.all()
        .annotate(
            total_submissions=Count('recipe_submissions', distinct=True),
            approved_submissions=Count(
                'recipe_submissions',
                filter=Q(recipe_submissions__status=RecipeSubmission.STATUS_APPROVED),
                distinct=True,
            ),
            rejected_submissions=Count(
                'recipe_submissions',
                filter=Q(recipe_submissions__status=RecipeSubmission.STATUS_REJECTED),
                distinct=True,
            ),
            pending_submissions=Count(
                'recipe_submissions',
                filter=Q(recipe_submissions__status=RecipeSubmission.STATUS_PENDING),
                distinct=True,
            ),
            total_recipes=Count('recipes', distinct=True),
            recipes_30d=Count('recipes', filter=Q(recipes__created_at__gte=month_ago), distinct=True),
            recipes_7d=Count('recipes', filter=Q(recipes__created_at__gte=week_ago), distinct=True),
        )
    )


def author_statistics_data(request):
    now = timezone.now()
    authors = _author_base_queryset(now).order_by('name')

    authors_payload = [
        {
            'id': a.id,
            'name': a.name,
            'total_submissions': a.total_submissions,
            'approved_submissions': a.approved_submissions,
            'rejected_submissions': a.rejected_submissions,
            'pending_submissions': a.pending_submissions,
            'total_recipes': a.total_recipes,
            'recipes_30d': a.recipes_30d,
            'recipes_7d': a.recipes_7d,
        }
        for a in authors
    ]

    start_30 = (now - timezone.timedelta(days=29)).date()
    daily = (
        RecipeSubmission.objects
        .filter(created_at__date__gte=start_30)
        .values('created_at__date')
        .annotate(total=Count('id'))
        .order_by('created_at__date')
    )
    daily_series = []
    for i in range(30):
        d = start_30 + timezone.timedelta(days=i)
        match = next((x for x in daily if x['created_at__date'] == d), None)
        daily_series.append({'day': d.isoformat(), 'total': match['total'] if match else 0})

    approved = RecipeSubmission.objects.filter(status=RecipeSubmission.STATUS_APPROVED).count()
    rejected = RecipeSubmission.objects.filter(status=RecipeSubmission.STATUS_REJECTED).count()

    leaderboard = list(
        _author_base_queryset(now)
        .order_by('-total_recipes', '-approved_submissions', 'name')
        .values('id', 'name', 'total_recipes', 'approved_submissions', 'total_submissions')[:10]
    )

    return JsonResponse({
        'authors': authors_payload,
        'daily_submissions_30d': daily_series,
        'approved_vs_rejected': {'approved': approved, 'rejected': rejected},
        'leaderboard': leaderboard,
    })


def author_statistics_export(request):
    now = timezone.now()
    authors = _author_base_queryset(now).order_by('name')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="author_statistics.csv"'
    writer = csv.writer(response)
    writer.writerow([
        'Author', 'Total Submissions', 'Approved', 'Rejected', 'Pending',
        'Total Recipes', 'Recipes (30 days)', 'Recipes (7 days)'
    ])
    for a in authors:
        writer.writerow([
            a.name, a.total_submissions, a.approved_submissions, a.rejected_submissions,
            a.pending_submissions, a.total_recipes, a.recipes_30d, a.recipes_7d
        ])
    return response
