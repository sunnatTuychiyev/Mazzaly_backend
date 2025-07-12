from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ("recipes", "0003_recipe_translations"),
    ]

    operations = [
        migrations.AddField(
            model_name="category",
            name="name_ru",
            field=models.CharField(max_length=100, blank=True, default=""),
        ),
        migrations.AddField(
            model_name="category",
            name="name_uz",
            field=models.CharField(max_length=100, blank=True, default=""),
        ),
    ]
