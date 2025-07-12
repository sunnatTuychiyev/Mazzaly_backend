from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ("recipes", "0002_remove_recipe_tags_ingredient_preparation_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="recipe",
            name="name_ru",
            field=models.CharField(max_length=255, blank=True, default=""),
        ),
        migrations.AddField(
            model_name="recipe",
            name="name_uz",
            field=models.CharField(max_length=255, blank=True, default=""),
        ),
        migrations.AddField(
            model_name="recipe",
            name="description_ru",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="recipe",
            name="description_uz",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="ingredient",
            name="name_ru",
            field=models.CharField(max_length=255, blank=True, default=""),
        ),
        migrations.AddField(
            model_name="ingredient",
            name="name_uz",
            field=models.CharField(max_length=255, blank=True, default=""),
        ),
        migrations.AddField(
            model_name="instruction",
            name="description_ru",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="instruction",
            name="description_uz",
            field=models.TextField(blank=True, default=""),
        ),
    ]
