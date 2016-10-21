# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-09-23 13:28
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import filer.fields.file


class Migration(migrations.Migration):

    dependencies = [
        ('filer', '0006_auto_20160623_1627'),
        ('post_office', '0003_auto_20160831_1555'),
        ('todos', '0004_entityimage'),
    ]

    operations = [
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, verbose_name='Name')),
                ('transition_target', models.CharField(max_length=50, verbose_name='Event')),
                ('mail_to', models.PositiveIntegerField(blank=True, default=None, null=True, verbose_name='Mail to')),
                ('mail_template', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='post_office.EmailTemplate', verbose_name='Template')),
            ],
            options={
                'ordering': ('transition_target', 'mail_to'),
                'verbose_name': 'Notification',
                'verbose_name_plural': 'Notifications',
            },
        ),
        migrations.CreateModel(
            name='NotificationAttachment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('attachment', filer.fields.file.FilerFileField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='email_attachment', to='filer.File', verbose_name='Attachment')),
                ('notification', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='todos.Notification')),
            ],
            options={
                'verbose_name': 'Attachment',
                'verbose_name_plural': 'Attachments',
            },
        ),
        migrations.AddField(
            model_name='todo',
            name='images',
            field=models.ManyToManyField(through='todos.EntityImage', to='filer.Image'),
        ),
        migrations.AlterUniqueTogether(
            name='entityrelation',
            unique_together=set([('term', 'from_entity', 'to_entity')]),
        ),
    ]