from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0009_recipe_created_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='mealplan',
            name='custom_meal',
            field=models.CharField(max_length=255, blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='mealplan',
            name='recipe',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='recipes.recipe', null=True, blank=True),
        ),
    ]
