from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("recommendations", "0003_align_generated_model_state")]

    operations = [
        migrations.AddField(
            model_name="food",
            name="staple_types",
            field=models.JSONField(default=list),
        ),
    ]
