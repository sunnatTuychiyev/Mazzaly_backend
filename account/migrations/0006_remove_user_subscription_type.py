from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('account', '0005_user_subscription_type'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='subscription_type',
        ),
    ]
