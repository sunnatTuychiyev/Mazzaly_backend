from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('analytics', '0002_sitevisit'),
    ]

    operations = [
        migrations.AddField(
            model_name='sitevisit',
            name='session_key',
            field=models.CharField(default='', max_length=40),
            preserve_default=False,
        ),
    ]
