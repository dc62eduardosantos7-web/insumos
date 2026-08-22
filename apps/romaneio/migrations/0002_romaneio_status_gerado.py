from django.db import migrations, models


def converter_status_romaneio(apps, schema_editor):
    Romaneio = apps.get_model("romaneio", "Romaneio")
    Romaneio.objects.exclude(status="CANCELADO").update(status="GERADO")


class Migration(migrations.Migration):
    dependencies = [
        ("romaneio", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(converter_status_romaneio, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="romaneio",
            name="status",
            field=models.CharField(
                choices=[
                    ("GERADO", "Gerado na separação"),
                    ("CANCELADO", "Cancelado"),
                ],
                default="GERADO",
                max_length=12,
            ),
        ),
    ]
