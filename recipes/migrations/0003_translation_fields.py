from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0002_remove_recipe_tags_ingredient_preparation_and_more'),
    ]

    operations = [
        # Recipe
        migrations.AddField(
            model_name='recipe',
            name='name_ru',
            field=models.CharField(max_length=255, blank=True, null=True),
        ),
        migrations.AddField(
            model_name='recipe',
            name='name_uz',
            field=models.CharField(max_length=255, blank=True, null=True),
        ),
        migrations.AddField(
            model_name='recipe',
            name='description_ru',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='recipe',
            name='description_uz',
            field=models.TextField(blank=True, null=True),
        ),
        # Category
        migrations.AddField(
            model_name='category',
            name='name_ru',
            field=models.CharField(max_length=100, blank=True, null=True),
        ),
        migrations.AddField(
            model_name='category',
            name='name_uz',
            field=models.CharField(max_length=100, blank=True, null=True),
        ),
        # MealType
        migrations.AddField(
            model_name='mealtype',
            name='name_ru',
            field=models.CharField(max_length=50, blank=True, null=True),
        ),
        migrations.AddField(
            model_name='mealtype',
            name='name_uz',
            field=models.CharField(max_length=50, blank=True, null=True),
        ),
        # Ingredient
        migrations.AddField(
            model_name='ingredient',
            name='name_ru',
            field=models.CharField(max_length=255, blank=True, null=True),
        ),
        migrations.AddField(
            model_name='ingredient',
            name='name_uz',
            field=models.CharField(max_length=255, blank=True, null=True),
        ),
        migrations.AddField(
            model_name='ingredient',
            name='preparation_ru',
            field=models.CharField(max_length=100, blank=True, null=True),
        ),
        migrations.AddField(
            model_name='ingredient',
            name='preparation_uz',
            field=models.CharField(max_length=100, blank=True, null=True),
        ),
        # Instruction
        migrations.AddField(
            model_name='instruction',
            name='description_ru',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='instruction',
            name='description_uz',
            field=models.TextField(blank=True, null=True),
        ),
    ]
