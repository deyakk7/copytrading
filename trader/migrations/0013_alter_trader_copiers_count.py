# Generated by Django 5.0.3 on 2024-04-11 18:01

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trader', '0012_alter_trader_max_copiers'),
    ]

    operations = [
        migrations.AlterField(
            model_name='trader',
            name='copiers_count',
            field=models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)]),
        ),
    ]
