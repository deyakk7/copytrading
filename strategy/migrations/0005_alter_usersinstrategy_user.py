# Generated by Django 5.0.3 on 2024-06-07 02:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('strategy', '0004_strategy_available_pool'),
    ]

    operations = [
        migrations.AlterField(
            model_name='usersinstrategy',
            name='user',
            field=models.CharField(max_length=100),
        ),
    ]
