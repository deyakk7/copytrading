# Generated by Django 5.0.3 on 2024-04-26 14:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trader', '0002_trader_deposit'),
    ]

    operations = [
        migrations.AddField(
            model_name='trader',
            name='trader_type',
            field=models.CharField(blank=True, choices=[('Conservative', 'conservative'), ('Trending', 'trending')], default=None, max_length=30, null=True),
        ),
    ]
