# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='CronJobLog',
            fields=[
                (
                    'id',
                    models.AutoField(
                        verbose_name='ID',
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                ('code', models.CharField(max_length=64, db_index=True)),
                ('start_time', models.DateTimeField(db_index=True)),
                ('end_time', models.DateTimeField(db_index=True)),
                ('is_success', models.BooleanField(default=False)),
                ('message', models.TextField(max_length=1000, blank=True)),
                (
                    'ran_at_time',
                    models.TimeField(
                        db_index=True, null=True, editable=False, blank=True
                    ),
                ),
            ],
            options={
                # These were historically created by an ``AlterIndexTogether``
                # operation (``index_together`` was removed in Django 5.1).
                # Existing installs keep their database-generated index names
                # until 0004 renames them to the explicit names below.
                'indexes': [
                    models.Index(
                        fields=['code', 'is_success', 'ran_at_time'],
                        name='dcron_code_succ_time_idx',
                    ),
                    models.Index(
                        fields=['code', 'start_time', 'ran_at_time'],
                        name='dcron_code_start_ran_idx',
                    ),
                    models.Index(
                        fields=['code', 'start_time'],
                        name='dcron_code_start_idx',
                    ),
                ],
            },
        ),
    ]
