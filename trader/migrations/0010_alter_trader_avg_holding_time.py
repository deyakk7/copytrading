# Generated by Django 5.0.3 on 2024-04-08 11:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trader', '0009_trader_roi_trader_win_rate'),
    ]

    operations = [
        migrations.AlterField(
            model_name='trader',
            name='avg_holding_time',
            field=models.CharField(default='No info', max_length=20),
        ),
    ]