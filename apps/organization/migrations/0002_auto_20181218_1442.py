# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2018-12-18 14:42
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('organization', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='courseorg',
            old_name='click_num',
            new_name='click_nums',
        ),
    ]
