# Generated by Django 5.0.3 on 2024-04-22 15:32

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('strategy', '0003_strategy_trader_deposit'),
    ]

    operations = [
        migrations.AddField(
            model_name='strategy',
            name='available_pool',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=30, validators=[django.core.validators.MinValueValidator(0)]),
        ),
    ]
