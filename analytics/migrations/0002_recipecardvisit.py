from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('analytics', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='RecipeCardVisit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ip_address', models.GenericIPAddressField()),
                ('user_agent', models.CharField(max_length=256)),
                ('period_start', models.DateTimeField()),
                ('period_type', models.CharField(max_length=4, choices=[('hour', 'Hour'), ('day', 'Day')])),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'unique_together': {('ip_address', 'user_agent', 'period_start', 'period_type')},
            },
        ),
    ]
