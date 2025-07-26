from django.utils import timezone
from django.db.models import Count
from django.contrib.sessions.models import Session
from django.http import JsonResponse

from recipes.models import Recipe
from account.models import User
from .models import RecipeViewLog


def statistics_data(request):
    """Return JSON data for statistics charts."""
    now = timezone.now()
    week_ago = now - timezone.timedelta(days=7)
    month_ago = now - timezone.timedelta(days=30)

    views_per_recipe = (
        Recipe.objects.annotate(total=Count('view_logs'))
        .values('name', 'total')
    )

    top_week = (
        Recipe.objects.filter(view_logs__timestamp__gte=week_ago)
        .annotate(total=Count('view_logs'))
        .order_by('-total')
        .values('name', 'total')[:5]
    )
    top_month = (
        Recipe.objects.filter(view_logs__timestamp__gte=month_ago)
        .annotate(total=Count('view_logs'))
        .order_by('-total')
        .values('name', 'total')[:5]
    )
    user_activity = (
        RecipeViewLog.objects.order_by('-timestamp')
        .select_related('user', 'recipe')
        .values('user__email', 'recipe__name', 'timestamp')[:100]
    )

    active_sessions = Session.objects.filter(expire_date__gte=now).count()
    total_users = User.objects.count()

    return JsonResponse({
        'views_per_recipe': list(views_per_recipe),
        'top_week': list(top_week),
        'top_month': list(top_month),
        'user_activity': list(user_activity),
        'active_sessions': active_sessions,
        'total_users': total_users,
    })
