from django.db import migrations, models
import django.utils.timezone
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('base', '0003_alter_lumber_options_remove_lumber_created_at_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='lumber',
            name='status',
            field=models.CharField(
                choices=[('Active', 'Active'), ('Expired', 'Expired'), ('Pending', 'Pending')],
                default='Pending',
                max_length=20
            ),
        ),
        migrations.AddField(
            model_name='lumber',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='lumber',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name='lumber',
            name='created_by',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to=settings.AUTH_USER_MODEL
            ),
        ),
        migrations.AlterField(
            model_name='lumber',
            name='species',
            field=models.CharField(
                choices=[
                    ('Molave', 'Molave'),
                    ('Sawn Lumber', 'Sawn Lumber'),
                    ('Fuel Wood', 'Fuel Wood'),
                    ('Yemane', 'Yemane'),
                    ('Mahogany', 'Mahogany'),
                    ('Narra', 'Narra'),
                    ('Minepoles', 'Minepoles'),
                    ('Teabolts', 'Teabolts')
                ],
                max_length=100
            ),
        ),
    ] 