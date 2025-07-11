from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0002_remove_recipe_tags_ingredient_preparation_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='recipe',
            name='name_en',
            field=models.CharField(max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='recipe',
            name='name_ru',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='recipe',
            name='name_uz',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='recipe',
            name='description_en',
            field=models.TextField(null=True),
        ),
        migrations.AddField(
            model_name='recipe',
            name='description_ru',
            field=models.TextField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='recipe',
            name='description_uz',
            field=models.TextField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='ingredient',
            name='name_en',
            field=models.CharField(max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='ingredient',
            name='name_ru',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='ingredient',
            name='name_uz',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='instruction',
            name='description_en',
            field=models.TextField(null=True),
        ),
        migrations.AddField(
            model_name='instruction',
            name='description_ru',
            field=models.TextField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='instruction',
            name='description_uz',
            field=models.TextField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='category',
            name='name_en',
            field=models.CharField(max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='category',
            name='name_ru',
            field=models.CharField(max_length=100, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='category',
            name='name_uz',
            field=models.CharField(max_length=100, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='mealtype',
            name='name_en',
            field=models.CharField(max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='mealtype',
            name='name_ru',
            field=models.CharField(max_length=50, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='mealtype',
            name='name_uz',
            field=models.CharField(max_length=50, null=True, blank=True),
        ),
    ]
