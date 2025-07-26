from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0007_set_plan_from_flags'),
    ]

    operations = [
        migrations.AddField(
            model_name='recipe',
            name='views',
            field=models.PositiveIntegerField(default=0, help_text='Number of times the recipe has been viewed'),
        ),
    ]
