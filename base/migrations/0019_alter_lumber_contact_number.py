# Generated by Django 5.1.6 on 2025-03-01 16:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0018_alter_lumber_brgy_alter_lumber_contact_number_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='lumber',
            name='contact_number',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
    ]
