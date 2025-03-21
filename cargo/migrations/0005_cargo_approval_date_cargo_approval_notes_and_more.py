# Generated by Django 5.1.5 on 2025-02-18 18:33

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cargo', '0004_alter_cargo_source_id_alter_cargo_source_type'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='cargo',
            name='approval_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='cargo',
            name='approval_notes',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='cargo',
            name='approved_by',
            field=models.ForeignKey(blank=True, limit_choices_to={'role': 'manager'}, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='approved_cargos', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='cargo',
            name='status',
            field=models.CharField(choices=[('draft', 'Draft'), ('pending_approval', 'Pending Manager Approval'), ('manager_approved', 'Approved by Manager'), ('pending', 'Pending Assignment'), ('assigned', 'Assigned to Carrier'), ('in_progress', 'In Progress'), ('completed', 'Completed'), ('cancelled', 'Cancelled'), ('rejected', 'Rejected by Manager'), ('expired', 'Expired')], default='draft', max_length=20),
        ),
        migrations.AlterField(
            model_name='cargostatushistory',
            name='status',
            field=models.CharField(choices=[('draft', 'Draft'), ('pending_approval', 'Pending Manager Approval'), ('manager_approved', 'Approved by Manager'), ('pending', 'Pending Assignment'), ('assigned', 'Assigned to Carrier'), ('in_progress', 'In Progress'), ('completed', 'Completed'), ('cancelled', 'Cancelled'), ('rejected', 'Rejected by Manager'), ('expired', 'Expired')], max_length=20),
        ),
    ]
