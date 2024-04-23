# Generated by Django 5.0.3 on 2024-04-19 12:09

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('strategy', '0002_strategy_saved_avg_profit'),
    ]

    operations = [
        migrations.AddField(
            model_name='strategy',
            name='trader_deposit',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=30, validators=[django.core.validators.MinValueValidator(0)]),
        ),
    ]