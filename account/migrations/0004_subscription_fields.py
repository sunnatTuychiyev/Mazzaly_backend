from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('account', '0003_add_telegram_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='subscription_type',
            field=models.CharField(default='Standard', max_length=10, choices=[('Standard', 'Standard'), ('Healthy', 'Healthy'), ('Premium', 'Premium')]),
        ),
        migrations.AddField(
            model_name='user',
            name='subscription_expiration',
            field=models.DateTimeField(null=True, blank=True),
        ),
    ]
