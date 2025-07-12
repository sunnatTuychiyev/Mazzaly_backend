from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ("recipes", "0002_remove_recipe_tags_ingredient_preparation_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="RecipeTranslation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("language", models.CharField(max_length=2, choices=[("en", "English"), ("ru", "Russian"), ("uz", "Uzbek")])),
                ("name", models.CharField(max_length=255)),
                ("description", models.TextField()),
                ("recipe", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="translations", to="recipes.recipe")),
            ],
            options={
                "unique_together": {("recipe", "language")},
            },
        ),
        migrations.CreateModel(
            name="IngredientTranslation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("language", models.CharField(max_length=2, choices=[("en", "English"), ("ru", "Russian"), ("uz", "Uzbek")])),
                ("name", models.CharField(max_length=255)),
                ("ingredient", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="translations", to="recipes.ingredient")),
            ],
            options={
                "unique_together": {("ingredient", "language")},
            },
        ),
        migrations.CreateModel(
            name="InstructionTranslation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("language", models.CharField(max_length=2, choices=[("en", "English"), ("ru", "Russian"), ("uz", "Uzbek")])),
                ("description", models.TextField()),
                ("instruction", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="translations", to="recipes.instruction")),
            ],
            options={
                "unique_together": {("instruction", "language")},
            },
        ),
    ]
