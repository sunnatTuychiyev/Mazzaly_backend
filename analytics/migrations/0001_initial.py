from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('recipes', '0001_initial'),
        ('account', '0006_remove_user_subscription_type'),
    ]

    operations = [
        migrations.CreateModel(
            name='RecipeViewLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('country', models.CharField(blank=True, default='', max_length=64)),
                ('recipe', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='view_logs', to='recipes.recipe')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='recipe_views', to='account.user')),
            ],
            options={'ordering': ['-timestamp']},
        ),
    ]
