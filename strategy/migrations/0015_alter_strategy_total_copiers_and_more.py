# Generated by Django 5.0.3 on 2024-04-11 18:01

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('strategy', '0014_remove_strategy_max_users'),
    ]

    operations = [
        migrations.AlterField(
            model_name='strategy',
            name='total_copiers',
            field=models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AlterField(
            model_name='strategy',
            name='total_deposited',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=30, validators=[django.core.validators.MinValueValidator(0)]),
        ),
    ]