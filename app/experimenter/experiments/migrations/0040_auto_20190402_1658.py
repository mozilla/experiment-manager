# Generated by Django 2.1.7 on 2019-04-02 16:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("experiments", "0039_auto_20190327_1816")]

    operations = [
        migrations.AlterField(
            model_name="experimentvariant",
            name="value",
            field=models.CharField(max_length=10240, null=True),
        )
    ]
