from django.test import TestCase, override_settings

from .models import User, Subscription


class SubscriptionSignalTests(TestCase):
    @override_settings(PROMO_PREMIUM_ON_SIGNUP=True)
    def test_new_user_gets_premium_then_standard_when_flag_enabled(self):
        user = User.objects.create_user(
            email='promo@example.com',
            first_name='Promo',
            last_name='User',
            password='StrongPass1',
        )

        self.assertEqual(user.subscriptions.count(), 2)

        premium, standard = user.subscriptions.order_by('start_date')

        self.assertEqual(premium.plan, Subscription.PLAN_PREMIUM)
        self.assertTrue(premium.end_date)

        self.assertEqual(standard.plan, Subscription.PLAN_STANDARD)
        self.assertEqual(standard.start_date, premium.end_date)

    @override_settings(PROMO_PREMIUM_ON_SIGNUP=False)
    def test_new_user_gets_only_standard_when_flag_disabled(self):
        user = User.objects.create_user(
            email='standard@example.com',
            first_name='Standard',
            last_name='User',
            password='StrongPass1',
        )

        self.assertEqual(user.subscriptions.count(), 1)

        sub = user.subscriptions.first()
        self.assertEqual(sub.plan, Subscription.PLAN_STANDARD)

    def test_existing_user_save_does_not_create_extra_subscriptions(self):
        user = User.objects.create_user(
            email='existing@example.com',
            first_name='Existing',
            last_name='User',
            password='StrongPass1',
        )

        original_count = user.subscriptions.count()

        user.first_name = 'Updated'
        user.save()

        self.assertEqual(user.subscriptions.count(), original_count)
