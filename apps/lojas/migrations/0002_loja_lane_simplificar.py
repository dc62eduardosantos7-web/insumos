from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("lojas", "0001_initial")]

    operations = [
        migrations.AddField(
            model_name="loja",
            name="lane",
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.RemoveField(model_name="loja", name="ativo"),
        migrations.RemoveField(model_name="loja", name="cidade"),
        migrations.RemoveField(model_name="loja", name="endereco"),
        migrations.RemoveField(model_name="loja", name="uf"),
    ]
