from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('analytics', '0003_sitevisit_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sitevisit',
            name='date',
            field=models.DateTimeField(auto_now_add=True),
        ),
    ]
