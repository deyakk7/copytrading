# Generated by Django 5.0.3 on 2024-04-29 23:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trader', '0005_trader_max_drawdown'),
    ]

    operations = [
        migrations.CreateModel(
            name='TrendingThreshold',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('min_copiers', models.IntegerField(default=10)),
            ],
        ),
    ]
