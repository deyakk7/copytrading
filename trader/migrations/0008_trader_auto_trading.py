# Generated by Django 5.0.3 on 2024-06-20 17:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trader', '0007_alter_trendingthreshold_min_copiers'),
    ]

    operations = [
        migrations.AddField(
            model_name='trader',
            name='auto_trading',
            field=models.BooleanField(default=False),
        ),
    ]