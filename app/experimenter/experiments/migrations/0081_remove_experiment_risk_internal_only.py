# Generated by Django 3.0.2 on 2020-02-05 23:53

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [("experiments", "0080_auto_20200124_1335")]

    operations = [
        migrations.RemoveField(model_name="experiment", name="risk_internal_only")
    ]
