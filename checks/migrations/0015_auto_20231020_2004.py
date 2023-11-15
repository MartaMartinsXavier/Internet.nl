# Generated by Django 3.2.20 on 2023-10-20 20:04

import checks.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('checks', '0014_auto_20230804_0855'),
    ]

    operations = [
        migrations.AddField(
            model_name='domaintestappsecpriv',
            name='server_header_enabled',
            field=models.BooleanField(default=False, null=True),
        ),
        migrations.AddField(
            model_name='domaintestappsecpriv',
            name='server_header_score',
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name='domaintestappsecpriv',
            name='server_header_values',
            field=checks.models.ListField(default=[]),
        ),
        migrations.AddField(
            model_name='domaintestappsecpriv',
            name='set_cookie_enabled',
            field=models.BooleanField(default=False, null=True),
        ),
        migrations.AddField(
            model_name='domaintestappsecpriv',
            name='set_cookie_score',
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name='domaintestappsecpriv',
            name='set_cookie_values',
            field=checks.models.ListField(default=[]),
        ),
    ]