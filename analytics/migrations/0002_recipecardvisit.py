from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('analytics', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='RecipeCardHourlyVisit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ip_address', models.GenericIPAddressField()),
                ('user_agent', models.CharField(max_length=256)),
                ('hour', models.DateTimeField()),
                ('created', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['-hour'],
                'unique_together': {('ip_address', 'user_agent', 'hour')},
            },
        ),
        migrations.CreateModel(
            name='RecipeCardDailyVisit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ip_address', models.GenericIPAddressField()),
                ('user_agent', models.CharField(max_length=256)),
                ('day', models.DateField()),
                ('created', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['-day'],
                'unique_together': {('ip_address', 'user_agent', 'day')},
            },
        ),
    ]
