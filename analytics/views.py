from django.utils import timezone
from django.db.models import Count
from django.db.models.functions import TruncDate
from django.contrib.sessions.models import Session
from django.http import JsonResponse, HttpResponse
from django.db.models import Q
from django.template.loader import get_template
from weasyprint import HTML

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

    views_per_day = (
        RecipeViewLog.objects.filter(timestamp__gte=week_ago)
        .annotate(day=TruncDate('timestamp'))
        .values('day')
        .annotate(total=Count('id'))
        .order_by('day')
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

    verified_users = User.objects.filter(is_email_verified=True).count()
    unverified_users = total_users - verified_users

    verified_premium = (
        User.objects.filter(
            is_email_verified=True,
            subscriptions__plan=Subscription.PLAN_PREMIUM,
            subscriptions__start_date__lte=now,
        )
        .filter(Q(subscriptions__end_date__isnull=True) | Q(subscriptions__end_date__gte=now))
        .distinct()
        .count()
    )
    verified_healthy = (
        User.objects.filter(
            is_email_verified=True,
            subscriptions__plan=Subscription.PLAN_HEALTHY,
            subscriptions__start_date__lte=now,
        )
        .filter(Q(subscriptions__end_date__isnull=True) | Q(subscriptions__end_date__gte=now))
        .distinct()
        .count()
    )
    verified_standard = verified_users - verified_premium - verified_healthy

    new_recipes = (
        Recipe.objects.filter(created_at__gte=month_ago)
        .annotate(day=TruncDate('created_at'))
        .values('day')
        .annotate(total=Count('id'))
        .order_by('day')
    )

    return JsonResponse({
        'views_per_recipe': list(views_per_recipe),
        'top_week': list(top_week),
        'top_month': list(top_month),
        'user_activity': list(user_activity),
        'active_sessions': active_sessions,
        'views_per_day': list(views_per_day),
        'new_recipes': list(new_recipes),
        'subscription_breakdown': {
            'total': total_users,
            'premium': premium_users,
            'healthy': healthy_users,
            'standard': standard_users,
        },
        'verification': {
            'verified': verified_users,
            'unverified': unverified_users,
            'verified_premium': verified_premium,
            'verified_healthy': verified_healthy,
            'verified_standard': verified_standard,
        },
    })


def monthly_report_pdf(request):
    """Generate a PDF report for the last month."""
    now = timezone.now()
    month_ago = now - timezone.timedelta(days=30)

    total_views = RecipeViewLog.objects.filter(timestamp__gte=month_ago).count()
    new_users = (
        User.objects.filter(recipe_views__timestamp__gte=month_ago)
        .values('id')
        .distinct()
        .count()
    )
    new_recipes = Recipe.objects.filter(created_at__gte=month_ago).count()

    template = get_template('monthly_report.html')
    html = template.render({
        'total_views': total_views,
        'new_users': new_users,
        'new_recipes': new_recipes,
        'generated': now,
    })
    pdf = HTML(string=html).write_pdf()
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="monthly_report.pdf"'
    return response
