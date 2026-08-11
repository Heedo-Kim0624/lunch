from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("recommendations", "0002_candidate_snapshot_and_event_idempotency"),
    ]

    operations = [
        migrations.RenameIndex(
            model_name="userfoodevent",
            new_name="recommendat_anonymo_57a2f3_idx",
            old_name="recommendat_anonymo_b09921_idx",
        ),
        migrations.RenameIndex(
            model_name="userfoodevent",
            new_name="recommendat_anonymo_3211bd_idx",
            old_name="recommendat_anonymo_3b2ba4_idx",
        ),
        migrations.AlterField(
            model_name="food",
            name="id",
            field=models.BigAutoField(
                auto_created=True,
                primary_key=True,
                serialize=False,
                verbose_name="ID",
            ),
        ),
        migrations.AlterField(
            model_name="recommendationexposure",
            name="id",
            field=models.BigAutoField(
                auto_created=True,
                primary_key=True,
                serialize=False,
                verbose_name="ID",
            ),
        ),
        migrations.AlterField(
            model_name="userfoodevent",
            name="id",
            field=models.BigAutoField(
                auto_created=True,
                primary_key=True,
                serialize=False,
                verbose_name="ID",
            ),
        ),
    ]

