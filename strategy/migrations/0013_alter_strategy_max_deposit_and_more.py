# Generated by Django 5.0.3 on 2024-04-04 19:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('strategy', '0012_usersinstrategy_current_custom_profit_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='strategy',
            name='max_deposit',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=30),
        ),
        migrations.AlterField(
            model_name='strategy',
            name='min_deposit',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=30),
        ),
        migrations.AlterField(
            model_name='strategy',
            name='total_deposited',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=30),
        ),
        migrations.AlterField(
            model_name='useroutstrategy',
            name='value',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=30),
        ),
        migrations.AlterField(
            model_name='usersinstrategy',
            name='value',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=30),
        ),
    ]
