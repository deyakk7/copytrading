# Generated by Django 5.0.3 on 2024-03-23 00:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('strategy', '0008_remove_strategy_current_users'),
    ]

    operations = [
        migrations.AddField(
            model_name='strategy',
            name='current_custom_profit',
            field=models.DecimalField(decimal_places=7, default=0, max_digits=30),
        ),
    ]