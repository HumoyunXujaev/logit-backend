# Generated by Django 5.1.5 on 2025-01-31 12:17

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Cargo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('description', models.TextField()),
                ('status', models.CharField(choices=[('draft', 'Draft'), ('active', 'Active'), ('in_progress', 'In Progress'), ('completed', 'Completed'), ('cancelled', 'Cancelled'), ('expired', 'Expired')], default='draft', max_length=20)),
                ('weight', models.DecimalField(decimal_places=2, max_digits=10, validators=[django.core.validators.MinValueValidator(0)])),
                ('volume', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, validators=[django.core.validators.MinValueValidator(0)])),
                ('length', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, validators=[django.core.validators.MinValueValidator(0)])),
                ('width', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, validators=[django.core.validators.MinValueValidator(0)])),
                ('height', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, validators=[django.core.validators.MinValueValidator(0)])),
                ('loading_point', models.CharField(max_length=255)),
                ('unloading_point', models.CharField(max_length=255)),
                ('additional_points', models.JSONField(blank=True, null=True)),
                ('loading_date', models.DateField()),
                ('is_constant', models.BooleanField(default=False)),
                ('is_ready', models.BooleanField(default=False)),
                ('vehicle_type', models.CharField(choices=[('tent', 'Tent'), ('refrigerator', 'Refrigerator'), ('isothermal', 'Isothermal'), ('container', 'Container'), ('car_carrier', 'Car Carrier'), ('board', 'Board')], max_length=20)),
                ('loading_type', models.CharField(choices=[('ramps', 'Ramps'), ('no_doors', 'No Doors'), ('side', 'Side Loading'), ('top', 'Top Loading'), ('hydro_board', 'Hydro Board')], max_length=20)),
                ('payment_method', models.CharField(choices=[('cash', 'Cash'), ('card', 'Card'), ('transfer', 'Bank Transfer'), ('advance', 'Advance')], max_length=20)),
                ('price', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('payment_details', models.JSONField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('views_count', models.PositiveIntegerField(default=0)),
                ('source_type', models.CharField(blank=True, max_length=50, null=True)),
                ('source_id', models.CharField(blank=True, max_length=100, null=True)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='CargoDocument',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(choices=[('invoice', 'Invoice'), ('cmr', 'CMR'), ('packing_list', 'Packing List'), ('other', 'Other')], max_length=20)),
                ('title', models.CharField(max_length=255)),
                ('file', models.FileField(upload_to='cargo_documents/')),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('notes', models.TextField(blank=True, null=True)),
            ],
            options={
                'ordering': ['-uploaded_at'],
            },
        ),
        migrations.CreateModel(
            name='CargoStatusHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('draft', 'Draft'), ('active', 'Active'), ('in_progress', 'In Progress'), ('completed', 'Completed'), ('cancelled', 'Cancelled'), ('expired', 'Expired')], max_length=20)),
                ('changed_at', models.DateTimeField(auto_now_add=True)),
                ('comment', models.TextField(blank=True, null=True)),
            ],
            options={
                'verbose_name_plural': 'Cargo status histories',
                'ordering': ['-changed_at'],
            },
        ),
    ]
