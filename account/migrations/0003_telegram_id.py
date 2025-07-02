from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('account', '0002_email_verification'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='telegram_id',
            field=models.BigIntegerField(null=True, blank=True, unique=True),
        ),
    ]
