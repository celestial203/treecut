from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('base', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='cutting',
            name='file',
            field=models.FileField(blank=True, null=True, upload_to='cutting_files/'),
        ),
    ] 