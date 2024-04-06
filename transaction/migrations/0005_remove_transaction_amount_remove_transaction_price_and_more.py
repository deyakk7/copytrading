# Generated by Django 5.0.3 on 2024-04-04 10:33

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transaction', '0004_userdeposit'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='transaction',
            name='amount',
        ),
        migrations.RemoveField(
            model_name='transaction',
            name='price',
        ),
        migrations.AddField(
            model_name='transaction',
            name='avg_open_price',
            field=models.DecimalField(decimal_places=7, default=0, max_digits=30),
        ),
        migrations.AddField(
            model_name='transaction',
            name='close_price',
            field=models.DecimalField(decimal_places=7, default=0, max_digits=30),
        ),
        migrations.AddField(
            model_name='transaction',
            name='close_time',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name='transaction',
            name='roi',
            field=models.DecimalField(decimal_places=7, default=0, max_digits=30),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='side',
            field=models.CharField(choices=[('short', 'short'), ('long', 'long')], default='long', max_length=10),
        ),
    ]