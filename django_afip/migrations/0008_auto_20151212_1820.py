# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2015-12-12 18:20
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('afip', '0007_auto_20151212_1754'),
    ]

    operations = [
        migrations.AlterField(
            model_name='receiptpdf',
            name='receipt',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='afip.Receipt', verbose_name='receipt'),
        ),
    ]
