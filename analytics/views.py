from django.utils import timezone
from django.db.models import Count
from django.db.models.functions import TruncDate, TruncHour
from django.contrib.sessions.models import Session
from django.http import JsonResponse, HttpResponse
from django.db.models import Q
from django.template.loader import get_template
from django.template.response import TemplateResponse
from weasyprint import HTML

from recipes.models import Recipe
from account.models import User, Subscription
from .models import RecipeViewLog, HourlyVisit, DailyVisit


def statistics_data(request):
    """Return JSON data for statistics charts."""
    now = timezone.now()
    week_ago = now - timezone.timedelta(days=7)
    month_ago = now - timezone.timedelta(days=30)
    hour_start = now.replace(minute=0, second=0, microsecond=0) - timezone.timedelta(hours=23)
    seven_days = now.date() - timezone.timedelta(days=6)
    thirty_days = now.date() - timezone.timedelta(days=29)

    views_per_recipe = (
        Recipe.objects.annotate(total=Count('view_logs'))
        .values('name', 'total')
    )

    hour_counts = {
        v['h']: v['total']
        for v in HourlyVisit.objects.filter(hour__gte=hour_start)
        .annotate(h=TruncHour('hour'))
        .values('h')
        .annotate(total=Count('id'))
    }
    hours = [hour_start + timezone.timedelta(hours=i) for i in range(24)]
    visits_24h = [
        {'hour': h.strftime('%H:%M'), 'total': hour_counts.get(h, 0)}
        for h in hours
    ]

    day_counts_7 = {
        v['day']: v['total']
        for v in DailyVisit.objects.filter(day__gte=seven_days)
        .values('day')
        .annotate(total=Count('id'))
    }
    days7 = [seven_days + timezone.timedelta(days=i) for i in range(7)]
    visits_7d = [
        {'day': d.isoformat(), 'total': day_counts_7.get(d, 0)}
        for d in days7
    ]

    day_counts_30 = {
        v['day']: v['total']
        for v in DailyVisit.objects.filter(day__gte=thirty_days)
        .values('day')
        .annotate(total=Count('id'))
    }
    days30 = [thirty_days + timezone.timedelta(days=i) for i in range(30)]
    visits_30d = [
        {'day': d.isoformat(), 'total': day_counts_30.get(d, 0)}
        for d in days30
    ]

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

    total_unique_visitors = DailyVisit.objects.values('ip_address', 'user_agent').distinct().count()

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
        'visits_24h': list(visits_24h),
        'visits_7d': list(visits_7d),
        'visits_30d': list(visits_30d),
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
        'total_unique_visitors': total_unique_visitors,
    })


def monthly_report_pdf(request):
    """Generate a PDF report for the selected month."""
    month_param = request.GET.get('month')
    if not month_param:
        # Show a simple form to choose the month
        return TemplateResponse(
            request,
            'report_month_select.html',
            {'title': 'Select Month'},
        )

    try:
        year, month = [int(p) for p in month_param.split('-')]
        start = timezone.datetime(year, month, 1)
    except (ValueError, TypeError):
        return TemplateResponse(
            request,
            'report_month_select.html',
            {'title': 'Select Month', 'error': 'Invalid month format'},
        )

    start = timezone.make_aware(start)
    if month == 12:
        end = timezone.datetime(year + 1, 1, 1)
    else:
        end = timezone.datetime(year, month + 1, 1)
    end = timezone.make_aware(end)

    total_views = RecipeViewLog.objects.filter(timestamp__gte=start, timestamp__lt=end).count()
    new_users = (
        User.objects.filter(recipe_views__timestamp__gte=start, recipe_views__timestamp__lt=end)
        .values('id')
        .distinct()
        .count()
    )
    new_recipes = Recipe.objects.filter(created_at__gte=start, created_at__lt=end).count()

    template = get_template('monthly_report.html')
    html = template.render(
        {
            'total_views': total_views,
            'new_users': new_users,
            'new_recipes': new_recipes,
            'generated': timezone.now(),
            'report_month': start.strftime('%B %Y'),
        }
    )
    pdf = HTML(string=html).write_pdf()
    response = HttpResponse(pdf, content_type='application/pdf')
    filename = f"report_{year}_{month:02d}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response
