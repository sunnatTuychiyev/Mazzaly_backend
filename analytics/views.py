from django.utils import timezone
from django.db.models import Count
from django.contrib.sessions.models import Session
from django.http import JsonResponse
from django.db.models import Q

from recipes.models import Recipe
from account.models import User, Subscription
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

    premium_users = (
        User.objects.filter(
            subscriptions__plan=Subscription.PLAN_PREMIUM,
            subscriptions__start_date__lte=now,
        )
        .filter(Q(subscriptions__end_date__isnull=True) | Q(subscriptions__end_date__gte=now))
        .distinct()
        .count()
    )

    healthy_users = (
        User.objects.filter(
            subscriptions__plan=Subscription.PLAN_HEALTHY,
            subscriptions__start_date__lte=now,
        )
        .filter(Q(subscriptions__end_date__isnull=True) | Q(subscriptions__end_date__gte=now))
        .distinct()
        .count()
    )

    standard_users = total_users - premium_users - healthy_users

    return JsonResponse({
        'views_per_recipe': list(views_per_recipe),
        'top_week': list(top_week),
        'top_month': list(top_month),
        'user_activity': list(user_activity),
        'active_sessions': active_sessions,
        'subscription_breakdown': {
            'total': total_users,
            'premium': premium_users,
            'healthy': healthy_users,
            'standard': standard_users,
        },
    })
