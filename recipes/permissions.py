from rest_framework import permissions
from account.models import Subscription

class IsHealthySubscriber(permissions.BasePermission):
    """Allow access only to Healthy or Premium subscribers"""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.current_plan in [Subscription.PLAN_HEALTHY, Subscription.PLAN_PREMIUM]

class IsPremiumSubscriber(permissions.BasePermission):
    """Allow access only to Premium subscribers"""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.current_plan == Subscription.PLAN_PREMIUM

