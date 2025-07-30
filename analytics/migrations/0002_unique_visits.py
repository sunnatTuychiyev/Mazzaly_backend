from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('analytics', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='HourlyVisit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ip_address', models.GenericIPAddressField()),
                ('user_agent', models.CharField(max_length=255)),
                ('hour', models.DateTimeField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={'ordering': ['hour']},
        ),
        migrations.CreateModel(
            name='DailyVisit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ip_address', models.GenericIPAddressField()),
                ('user_agent', models.CharField(max_length=255)),
                ('day', models.DateField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={'ordering': ['day']},
        ),
        migrations.AddConstraint(
            model_name='hourlyvisit',
            constraint=models.UniqueConstraint(fields=('ip_address', 'user_agent', 'hour'), name='unique_hour_visit'),
        ),
        migrations.AddConstraint(
            model_name='dailyvisit',
            constraint=models.UniqueConstraint(fields=('ip_address', 'user_agent', 'day'), name='unique_day_visit'),
        ),
    ]
