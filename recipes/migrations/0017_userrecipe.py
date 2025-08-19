# Generated manually for UserRecipe model
from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0016_rename_title_recipesubmission_name_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='UserRecipe',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('image', models.URLField(blank=True, null=True)),
                ('status', models.CharField(choices=[('pending', 'pending'), ('approved', 'approved'), ('rejected', 'rejected')], default='pending', max_length=16)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('telegram_user_id', models.BigIntegerField(blank=True, null=True)),
                ('owner', models.ForeignKey(on_delete=models.CASCADE, related_name='user_recipes', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
