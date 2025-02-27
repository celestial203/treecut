# Generated by Django 5.1.6 on 2025-02-21 12:46

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0003_cuttingrecord_number_of_trees'),
    ]

    operations = [
        migrations.AddField(
            model_name='cutting',
            name='latitude',
            field=models.DecimalField(blank=True, decimal_places=6, help_text='Enter latitude between -90 and 90 degrees', max_digits=9, null=True, validators=[django.core.validators.MinValueValidator(-90), django.core.validators.MaxValueValidator(90)]),
        ),
        migrations.AddField(
            model_name='cutting',
            name='longitude',
            field=models.DecimalField(blank=True, decimal_places=6, help_text='Enter longitude between -180 and 180 degrees', max_digits=9, null=True, validators=[django.core.validators.MinValueValidator(-180), django.core.validators.MaxValueValidator(180)]),
        ),
    ]
