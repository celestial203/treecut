# Generated by Django 5.1.6 on 2025-02-25 02:39

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0014_remove_cuttingrecord__remaining_balance_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='cuttingrecord',
            name='date',
            field=models.DateField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name='cuttingrecord',
            name='volume_type',
            field=models.CharField(choices=[('Initial', 'Initial'), ('Additional', 'Additional')], default='Initial', max_length=20),
        ),
        migrations.AlterField(
            model_name='cuttingrecord',
            name='parent_tcp',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='cutting_records', to='base.cutting'),
        ),
        migrations.CreateModel(
            name='VolumeRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('volume_type', models.CharField(choices=[('Initial', 'Initial'), ('Additional', 'Additional')], max_length=20)),
                ('volume', models.DecimalField(decimal_places=2, max_digits=10)),
                ('remarks', models.TextField(blank=True, null=True)),
                ('cutting', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='volume_records', to='base.cutting')),
            ],
            options={
                'ordering': ['-date'],
            },
        ),
    ]
