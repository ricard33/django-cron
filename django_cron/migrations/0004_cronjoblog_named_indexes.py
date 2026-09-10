# Give the three CronJobLog composite indexes explicit names.
#
# They used to be declared with ``Meta.index_together`` (created by the
# ``AlterIndexTogether`` operation in 0001 with database-generated names).
# ``index_together`` was removed in Django 5.1, so the model now declares them
# as ``Meta.indexes`` with explicit names -- this migration renames the existing
# implicit indexes to match. ``RenameIndex`` with ``old_fields`` locates the
# index by its columns and is a no-op when it is already named as expected
# (fresh installs).
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("django_cron", "0003_cronjoblock"),
    ]

    operations = [
        migrations.RenameIndex(
            model_name="cronjoblog",
            new_name="dcron_code_succ_time_idx",
            old_fields=("code", "is_success", "ran_at_time"),
        ),
        migrations.RenameIndex(
            model_name="cronjoblog",
            new_name="dcron_code_start_ran_idx",
            old_fields=("code", "start_time", "ran_at_time"),
        ),
        migrations.RenameIndex(
            model_name="cronjoblog",
            new_name="dcron_code_start_idx",
            old_fields=("code", "start_time"),
        ),
    ]
