from django.db import migrations, models
import django.utils.timezone

class Migration(migrations.Migration):

    dependencies = [
        ('analytics', '0002_sitevisit'),
    ]

    operations = [
        migrations.AddField(
            model_name='sitevisit',
            name='date',
            field=models.DateField(default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='sitevisit',
            name='session_key',
            field=models.CharField(max_length=40),
        ),
        migrations.AlterUniqueTogether(
            name='sitevisit',
            unique_together={('session_key', 'date')},
        ),
    ]
