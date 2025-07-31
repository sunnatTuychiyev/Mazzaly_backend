from django.db import migrations


def create_defaults(apps, schema_editor):
    MealType = apps.get_model('recipes', 'MealType')
    for name in ['breakfast', 'lunch', 'dinner']:
        MealType.objects.get_or_create(name=name)


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0010_mealplan_custom_meal'),
    ]

    operations = [
        migrations.RunPython(create_defaults, migrations.RunPython.noop),
    ]
