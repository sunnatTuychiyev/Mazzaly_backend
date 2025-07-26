from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0005_recipe_premium'),
        ('account', '0004_subscription'),
    ]

    operations = [
        migrations.AddField(
            model_name='recipe',
            name='subscription_plan',
            field=models.CharField(
                max_length=20,
                choices=[('standard','Standard'),('healthy','Healthy'),('premium','Premium')],
                default='standard',
            ),
        ),
    ]

