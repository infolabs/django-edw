# -*- coding: utf-8 -*-
# Generated by Django 1.9.8 on 2016-12-08 11:16
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('edw', '0049_auto_20161129_2143'),
    ]

    operations = [
        migrations.AddField(
            model_name='message',
            name='is_draft',
            field=models.BooleanField(default=True, verbose_name='Is draft'),
        ),
    ]
