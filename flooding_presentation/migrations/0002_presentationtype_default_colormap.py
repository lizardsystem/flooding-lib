# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('flooding_lib', '0001_initial'),
        ('flooding_presentation', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='presentationtype',
            name='default_colormap',
            field=models.ForeignKey(blank=True, to='flooding_lib.Colormap', null=True),
            preserve_default=True,
        ),
    ]
