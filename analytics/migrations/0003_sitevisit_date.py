from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('analytics', '0002_recipecardvisit'),
    ]

    operations = [
        migrations.CreateModel(
            name='SiteVisit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(auto_now_add=True)),
                ('ip_address', models.GenericIPAddressField()),
            ],
            options={'ordering': ['-date']},
        ),
    ]
