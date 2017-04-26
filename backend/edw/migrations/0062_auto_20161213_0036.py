# -*- coding: utf-8 -*-
# Generated by Django 1.9.8 on 2016-12-12 21:36
from __future__ import unicode_literals

from django.db import migrations
import django_fsm


class Migration(migrations.Migration):

    dependencies = [
        ('edw', '0061_auto_20161213_0035'),
    ]

    operations = [
        migrations.AlterField(
            model_name='particularproblem',
            name='status',
            field=django_fsm.FSMField(default='draft', max_length=50, protected=True, verbose_name='Status'),
        ),
    ]
