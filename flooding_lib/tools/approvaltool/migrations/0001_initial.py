# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ApprovalObject',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ApprovalObjectLog',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date', models.DateTimeField(auto_now_add=True)),
                ('creatorlog', models.CharField(max_length=40)),
                ('successful', models.NullBooleanField()),
                ('remarks', models.TextField(blank=True)),
                ('approvalobject', models.ForeignKey(to='approvaltool.ApprovalObject')),
            ],
            options={
                'get_latest_by': 'date',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ApprovalObjectState',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date', models.DateTimeField(auto_now_add=True)),
                ('creatorlog', models.CharField(max_length=40)),
                ('successful', models.NullBooleanField()),
                ('remarks', models.TextField(blank=True)),
                ('approvalobject', models.ForeignKey(to='approvaltool.ApprovalObject')),
            ],
            options={
                'get_latest_by': 'date',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ApprovalObjectType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=200)),
                ('type', models.IntegerField(unique=True, choices=[(1, 'Project'), (2, 'ROR'), (3, 'Rural use')])),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ApprovalRule',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=80)),
                ('description', models.TextField(blank=True)),
                ('position', models.IntegerField(default=0)),
                ('permissionlevel', models.IntegerField(default=1, help_text='Permission level of user for performing this task')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='approvalobjecttype',
            name='approvalrule',
            field=models.ManyToManyField(to='approvaltool.ApprovalRule'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='approvalobjectstate',
            name='approvalrule',
            field=models.ForeignKey(to='approvaltool.ApprovalRule'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='approvalobjectstate',
            unique_together=set([('approvalobject', 'approvalrule')]),
        ),
        migrations.AddField(
            model_name='approvalobjectlog',
            name='approvalrule',
            field=models.ForeignKey(to='approvaltool.ApprovalRule'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='approvalobject',
            name='approvalobjecttype',
            field=models.ManyToManyField(to='approvaltool.ApprovalObjectType'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='approvalobject',
            name='approvalrule',
            field=models.ManyToManyField(to='approvaltool.ApprovalRule', through='approvaltool.ApprovalObjectState'),
            preserve_default=True,
        ),
    ]
