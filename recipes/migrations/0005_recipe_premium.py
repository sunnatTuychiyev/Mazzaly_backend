from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0004_category_translations'),
    ]

    operations = [
        migrations.AddField(
            model_name='recipe',
            name='premium',
            field=models.BooleanField(default=False, help_text='Show as Premium Recipe'),
        ),
    ]

