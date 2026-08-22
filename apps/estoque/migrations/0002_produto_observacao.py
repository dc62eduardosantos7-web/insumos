from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("estoque", "0001_initial")]
    operations = [
        migrations.AddField(
            model_name="produto",
            name="observacao",
            field=models.TextField(blank=True, verbose_name="observação"),
        )
    ]
