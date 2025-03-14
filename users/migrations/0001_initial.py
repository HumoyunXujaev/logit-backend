# Generated by Django 5.1.5 on 2025-01-31 12:17

import django.core.validators
import django.db.models.deletion
import django.utils.timezone
import simple_history.models
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('telegram_id', models.CharField(max_length=100, primary_key=True, serialize=False, unique=True, verbose_name='Telegram ID')),
                ('first_name', models.CharField(max_length=255, verbose_name='First Name')),
                ('last_name', models.CharField(blank=True, max_length=255, verbose_name='Last Name')),
                ('username', models.CharField(blank=True, max_length=255, verbose_name='Username')),
                ('language_code', models.CharField(blank=True, max_length=10, verbose_name='Language Code')),
                ('is_active', models.BooleanField(default=True, verbose_name='Active')),
                ('is_staff', models.BooleanField(default=False, verbose_name='Staff status')),
                ('is_verified', models.BooleanField(default=False, verbose_name='Verified')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Date joined')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='Last login')),
                ('type', models.CharField(blank=True, choices=[('individual', 'Individual'), ('legal', 'Legal Entity')], max_length=20, null=True)),
                ('role', models.CharField(blank=True, choices=[('student', 'Student'), ('carrier', 'Carrier'), ('cargo-owner', 'Cargo Owner'), ('logistics-company', 'Logistics Company'), ('transport-company', 'Transport Company'), ('logit-trans', 'Logit Trans')], max_length=20, null=True)),
                ('preferred_language', models.CharField(choices=[('ru', 'Russian'), ('uz', 'Uzbek')], default='ru', max_length=2)),
                ('phone_number', models.CharField(blank=True, max_length=20, null=True)),
                ('whatsapp_number', models.CharField(blank=True, max_length=20, null=True)),
                ('company_name', models.CharField(blank=True, max_length=255, null=True)),
                ('position', models.CharField(blank=True, max_length=100, null=True)),
                ('registration_certificate', models.FileField(blank=True, null=True, upload_to='certificates/')),
                ('student_id', models.CharField(blank=True, max_length=50, null=True)),
                ('group_name', models.CharField(blank=True, max_length=100, null=True)),
                ('study_language', models.CharField(blank=True, max_length=50, null=True)),
                ('curator_name', models.CharField(blank=True, max_length=100, null=True)),
                ('end_date', models.DateField(blank=True, null=True)),
                ('verification_date', models.DateTimeField(blank=True, null=True)),
                ('verification_status', models.CharField(blank=True, max_length=50, null=True)),
                ('verification_notes', models.TextField(blank=True, null=True)),
                ('rating', models.DecimalField(decimal_places=2, default=0, max_digits=3, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(5)])),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
            ],
            options={
                'verbose_name': 'user',
                'verbose_name_plural': 'users',
                'ordering': ['-date_joined'],
            },
        ),
        migrations.CreateModel(
            name='HistoricalUser',
            fields=[
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('telegram_id', models.CharField(db_index=True, max_length=100, verbose_name='Telegram ID')),
                ('first_name', models.CharField(max_length=255, verbose_name='First Name')),
                ('last_name', models.CharField(blank=True, max_length=255, verbose_name='Last Name')),
                ('username', models.CharField(blank=True, max_length=255, verbose_name='Username')),
                ('language_code', models.CharField(blank=True, max_length=10, verbose_name='Language Code')),
                ('is_active', models.BooleanField(default=True, verbose_name='Active')),
                ('is_staff', models.BooleanField(default=False, verbose_name='Staff status')),
                ('is_verified', models.BooleanField(default=False, verbose_name='Verified')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Date joined')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='Last login')),
                ('type', models.CharField(blank=True, choices=[('individual', 'Individual'), ('legal', 'Legal Entity')], max_length=20, null=True)),
                ('role', models.CharField(blank=True, choices=[('student', 'Student'), ('carrier', 'Carrier'), ('cargo-owner', 'Cargo Owner'), ('logistics-company', 'Logistics Company'), ('transport-company', 'Transport Company'), ('logit-trans', 'Logit Trans')], max_length=20, null=True)),
                ('preferred_language', models.CharField(choices=[('ru', 'Russian'), ('uz', 'Uzbek')], default='ru', max_length=2)),
                ('phone_number', models.CharField(blank=True, max_length=20, null=True)),
                ('whatsapp_number', models.CharField(blank=True, max_length=20, null=True)),
                ('company_name', models.CharField(blank=True, max_length=255, null=True)),
                ('position', models.CharField(blank=True, max_length=100, null=True)),
                ('registration_certificate', models.TextField(blank=True, max_length=100, null=True)),
                ('student_id', models.CharField(blank=True, max_length=50, null=True)),
                ('group_name', models.CharField(blank=True, max_length=100, null=True)),
                ('study_language', models.CharField(blank=True, max_length=50, null=True)),
                ('curator_name', models.CharField(blank=True, max_length=100, null=True)),
                ('end_date', models.DateField(blank=True, null=True)),
                ('verification_date', models.DateTimeField(blank=True, null=True)),
                ('verification_status', models.CharField(blank=True, max_length=50, null=True)),
                ('verification_notes', models.TextField(blank=True, null=True)),
                ('rating', models.DecimalField(decimal_places=2, default=0, max_digits=3, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(5)])),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField(db_index=True)),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'historical user',
                'verbose_name_plural': 'historical users',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': ('history_date', 'history_id'),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name='HistoricalUserDocument',
            fields=[
                ('id', models.BigIntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('type', models.CharField(choices=[('driver_license', 'Driver License'), ('passport', 'Passport'), ('company_certificate', 'Company Certificate'), ('other', 'Other')], max_length=50)),
                ('title', models.CharField(max_length=255)),
                ('file', models.TextField(max_length=100)),
                ('uploaded_at', models.DateTimeField(blank=True, editable=False)),
                ('verified', models.BooleanField(default=False)),
                ('verified_at', models.DateTimeField(blank=True, null=True)),
                ('notes', models.TextField(blank=True, null=True)),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField(db_index=True)),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('user', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('verified_by', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'historical user document',
                'verbose_name_plural': 'historical user documents',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': ('history_date', 'history_id'),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name='UserDocument',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(choices=[('driver_license', 'Driver License'), ('passport', 'Passport'), ('company_certificate', 'Company Certificate'), ('other', 'Other')], max_length=50)),
                ('title', models.CharField(max_length=255)),
                ('file', models.FileField(upload_to='user_documents/')),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('verified', models.BooleanField(default=False)),
                ('verified_at', models.DateTimeField(blank=True, null=True)),
                ('notes', models.TextField(blank=True, null=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='documents', to=settings.AUTH_USER_MODEL)),
                ('verified_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='verified_documents', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-uploaded_at'],
            },
        ),
        migrations.AddIndex(
            model_name='user',
            index=models.Index(fields=['telegram_id'], name='users_user_telegra_b51e4c_idx'),
        ),
        migrations.AddIndex(
            model_name='user',
            index=models.Index(fields=['role'], name='users_user_role_36d76d_idx'),
        ),
        migrations.AddIndex(
            model_name='user',
            index=models.Index(fields=['type'], name='users_user_type_3fc058_idx'),
        ),
        migrations.AddIndex(
            model_name='userdocument',
            index=models.Index(fields=['user', 'type'], name='users_userd_user_id_3de1e7_idx'),
        ),
        migrations.AddIndex(
            model_name='userdocument',
            index=models.Index(fields=['verified'], name='users_userd_verifie_6f27ec_idx'),
        ),
    ]
