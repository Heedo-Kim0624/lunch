from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("recommendations", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="recommendationsession",
            name="candidate_snapshot",
            field=models.JSONField(default=list),
        ),
        migrations.AddConstraint(
            model_name="userfoodevent",
            constraint=models.UniqueConstraint(
                condition=models.Q(("exposure__isnull", False)),
                fields=("exposure", "event_type"),
                name="unique_exposure_event_type",
            ),
        ),
    ]

