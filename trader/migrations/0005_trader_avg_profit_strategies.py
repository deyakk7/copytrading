# Generated by Django 5.0.3 on 2024-03-19 22:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trader', '0004_trader_copiers_count_trader_followers_count_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='trader',
            name='avg_profit_strategies',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=5),
        ),
    ]
