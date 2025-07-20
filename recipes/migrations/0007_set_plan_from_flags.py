from django.db import migrations


def forwards(apps, schema_editor):
    Recipe = apps.get_model('recipes', 'Recipe')
    Recipe.objects.filter(premium=True).update(subscription_plan='premium')
    Recipe.objects.filter(premium=False, healthy=True).update(subscription_plan='healthy')


def backwards(apps, schema_editor):
    # No reasonable reverse
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0006_add_subscription_plan_field'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
