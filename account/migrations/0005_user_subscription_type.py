from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('account', '0004_subscription'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='subscription_type',
            field=models.CharField(
                max_length=20,
                choices=[('standard', 'Standard'), ('healthy', 'Healthy'), ('premium', 'Premium')],
                default='standard',
            ),
        ),
    ]
