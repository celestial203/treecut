# Generated by Django 5.1.6 on 2025-05-07 13:26

import django.core.validators
import django.db.models.deletion
import django.utils.timezone
from decimal import Decimal
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Chainsaw',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('no', models.CharField(max_length=50)),
                ('year', models.IntegerField()),
                ('region', models.CharField(max_length=50)),
                ('penro', models.CharField(max_length=100)),
                ('cenro', models.CharField(max_length=100)),
                ('province', models.CharField(max_length=100)),
                ('name', models.CharField(max_length=200)),
                ('municipality', models.CharField(max_length=100)),
                ('brand', models.CharField(max_length=100)),
                ('model', models.CharField(max_length=100)),
                ('serial_number', models.CharField(max_length=100)),
                ('purpose', models.CharField(choices=[('CUTTING IN PRIVATE PLANTATION FOR COMMERCIAL USE', 'CUTTING IN PRIVATE PLANTATION FOR COMMERCIAL USE'), ('CUTTING IN TENURE AREA FOR PERSONAL/NON COMMERCIAL USE', 'CUTTING IN TENURE AREA FOR PERSONAL/NON COMMERCIAL USE')], max_length=100)),
                ('date_acquired', models.DateField(blank=True, null=True)),
                ('cert_reg_number', models.CharField(max_length=100)),
                ('color', models.CharField(max_length=50)),
                ('registration_status', models.CharField(choices=[('NEW', 'NEW'), ('RENEWED', 'RENEWED'), ('RENEWAL', 'RENEWAL'), ('EXPIRED', 'EXPIRED')], max_length=50)),
                ('date_renewal', models.DateField(blank=True, null=True)),
                ('horse_power', models.CharField(max_length=50)),
                ('guidebar_length', models.CharField(max_length=50)),
                ('denr_sticker', models.CharField(max_length=100)),
                ('ctpo_number', models.CharField(max_length=100)),
                ('date_issued', models.DateField()),
                ('expiry_date', models.DateField()),
                ('file', models.FileField(blank=True, null=True, upload_to='chainsaw_files/')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='Cutting',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('permit_type', models.CharField(choices=[('TCP', 'TCP'), ('PLTP', 'PLTP'), ('STCP', 'STCP'), ('SPLTP', 'SPLTP')], default='TCP', max_length=100)),
                ('permit_number', models.CharField(max_length=100)),
                ('date_issued', models.DateField()),
                ('expiry_date', models.DateField()),
                ('permittee', models.CharField(max_length=200)),
                ('rep_by', models.CharField(blank=True, max_length=200, null=True)),
                ('location', models.TextField(blank=True, null=True)),
                ('latitude', models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                ('longitude', models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                ('tct_oct_no', models.CharField(blank=True, max_length=100, null=True)),
                ('tax_dec_no', models.CharField(blank=True, max_length=100, null=True)),
                ('lot_no', models.CharField(blank=True, max_length=100, null=True)),
                ('area', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('species', models.TextField(blank=True, null=True)),
                ('no_of_trees', models.IntegerField(default=0)),
                ('total_volume_granted', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('gross_volume', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('net_volume', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('permit_file', models.FileField(blank=True, null=True, upload_to='permits/')),
                ('status', models.CharField(choices=[('ACTIVE', 'Active'), ('EXPIRED', 'Expired'), ('CONSUMED', 'Consumed'), ('PENDING', 'Pending'), ('Active', 'Active'), ('Expired', 'Expired'), ('Pending', 'Pending')], default='PENDING', max_length=20)),
                ('situation', models.CharField(choices=[('ACTIVE', 'Active'), ('EXPIRED', 'Expired'), ('CONSUMED', 'Consumed'), ('PENDING', 'Pending'), ('Active', 'Active'), ('Expired', 'Expired'), ('Pending', 'Pending')], default='Pending', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('other_species', models.CharField(blank=True, max_length=255, null=True)),
                ('file', models.FileField(blank=True, null=True, upload_to='cutting_files/')),
                ('contact_number', models.CharField(blank=True, max_length=11, null=True)),
                ('or_number', models.CharField(blank=True, max_length=100, null=True)),
                ('payment_date', models.DateField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='CuttingPermit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('longitude', models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                ('latitude', models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Wood',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('type', models.CharField(choices=[('Resawmill-new', 'RESAWMILL-NEW'), ('Resawmill-renew', 'RESAWMILL-RENEWAL')], max_length=50)),
                ('wpp_number', models.CharField(max_length=100)),
                ('business_name', models.CharField(blank=True, default='Default Business Name', max_length=255, null=True)),
                ('address', models.CharField(blank=True, default='', max_length=255, null=True)),
                ('drc', models.DecimalField(decimal_places=2, max_digits=10)),
                ('alr', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('longitude', models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                ('latitude', models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                ('supplier_info', models.TextField(blank=True, null=True)),
                ('local_volume', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('imported_volume', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('area', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('approved_by', models.CharField(default='CENRO', max_length=255)),
                ('date_issued', models.DateField()),
                ('date_released', models.DateField()),
                ('expiry_date', models.DateField(blank=True, null=True)),
                ('wood_status', models.CharField(choices=[('ACTIVE_NEW', 'Active (New)'), ('ACTIVE_RENEWED', 'Active (Renewed)'), ('EXPIRED', 'Expired'), ('SUSPENDED', 'Suspended'), ('CANCELLED', 'Cancelled')], default='ACTIVE_NEW', max_length=20)),
                ('attachment', models.FileField(blank=True, null=True, upload_to='wood_attachments/')),
            ],
            options={
                'db_table': 'base_wood',
            },
        ),
        migrations.CreateModel(
            name='WoodProcessingPlant',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('address', models.TextField()),
                ('owner', models.CharField(max_length=255)),
                ('permit_number', models.CharField(max_length=100)),
                ('issue_date', models.DateField()),
                ('expiry_date', models.DateField()),
                ('status', models.CharField(choices=[('ACTIVE_NEW', 'Active (New)'), ('ACTIVE_RENEWED', 'Active (Renewed)'), ('EXPIRED', 'Expired'), ('SUSPENDED', 'Suspended'), ('CANCELLED', 'Cancelled')], default='ACTIVE_NEW', max_length=20)),
            ],
        ),
        migrations.CreateModel(
            name='CuttingRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(default=django.utils.timezone.now)),
                ('volume_type', models.CharField(choices=[('Initial', 'Initial'), ('Additional', 'Additional')], default='Initial', max_length=20)),
                ('species', models.CharField(choices=[('Molave', 'Molave'), ('Sawn Lumber', 'Sawn Lumber'), ('Fuel Wood', 'Fuel Wood'), ('Yemane', 'Yemane'), ('Mahogany', 'Mahogany'), ('Narra', 'Narra'), ('Minepoles', 'Minepoles'), ('Teabolts', 'Teabolts'), ('Others', 'Others')], default='Molave', max_length=100)),
                ('other_species', models.CharField(blank=True, max_length=100, null=True)),
                ('volume', models.DecimalField(decimal_places=2, max_digits=10)),
                ('calculated_volume', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('remaining_balance', models.DecimalField(blank=True, decimal_places=2, default=Decimal('0.00'), max_digits=10, null=True)),
                ('number_of_trees', models.IntegerField()),
                ('remarks', models.TextField(blank=True, null=True)),
                ('date_added', models.DateTimeField(auto_now_add=True)),
                ('parent_tcp', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='cutting_records', to='base.cutting')),
            ],
            options={
                'ordering': ['-date_added'],
            },
        ),
        migrations.CreateModel(
            name='Lumber',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('no', models.IntegerField(blank=True, null=True)),
                ('trade_name', models.CharField(max_length=100)),
                ('manager_owner', models.CharField(max_length=100)),
                ('contact_number', models.CharField(blank=True, max_length=11, null=True)),
                ('gender', models.CharField(choices=[('Male', 'Male'), ('Female', 'Female')], max_length=10)),
                ('brgy', models.CharField(max_length=100)),
                ('municipality', models.CharField(max_length=100)),
                ('province', models.CharField(max_length=100)),
                ('source_supplier', models.CharField(max_length=100)),
                ('permit_no', models.CharField(max_length=100)),
                ('date_issued', models.DateField()),
                ('expiry_date', models.DateField(blank=True, null=True)),
                ('volume_cubic_meter', models.DecimalField(decimal_places=2, max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal('0.01'))])),
                ('species', models.CharField(max_length=100)),
                ('file', models.FileField(blank=True, null=True, upload_to='lumber_files/')),
                ('status', models.CharField(choices=[('Active', 'Active'), ('Expired', 'Expired'), ('Pending', 'Pending')], default='Pending', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='lumber_records', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-date_issued'],
            },
        ),
        migrations.CreateModel(
            name='TreeSpecies',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('species', models.CharField(max_length=100)),
                ('quantity', models.IntegerField()),
                ('volume', models.DecimalField(blank=True, decimal_places=2, default=0.0, max_digits=10, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('cutting', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tree_species', to='base.cutting')),
            ],
            options={
                'verbose_name_plural': 'Tree Species',
                'ordering': ['species'],
            },
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='VolumeRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(default=django.utils.timezone.now)),
                ('species', models.CharField(choices=[('Sawn Lumber', 'Sawn Lumber'), ('Fuel Wood', 'Fuel Wood'), ('Minepoles', 'Minepoles'), ('Molave', 'Molave'), ('Yemane', 'Yemane'), ('Mahogany', 'Mahogany'), ('Narra', 'Narra'), ('Logbolts', 'Logbolts'), ('Others', 'Others')], max_length=100)),
                ('other_species', models.CharField(blank=True, max_length=100, null=True)),
                ('number_of_trees', models.IntegerField()),
                ('volume', models.DecimalField(decimal_places=2, max_digits=10)),
                ('calculated_volume', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('remaining_balance', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('remarks', models.TextField(blank=True, null=True)),
                ('date_added', models.DateTimeField(auto_now_add=True)),
                ('attachment', models.FileField(blank=True, null=True, upload_to='volume_records/')),
                ('cutting', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='volume_records', to='base.cutting')),
            ],
            options={
                'db_table': 'base_volumerecord',
                'ordering': ['-date_added'],
            },
        ),
    ]
