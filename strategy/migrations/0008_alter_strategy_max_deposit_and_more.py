# Generated by Django 5.0.3 on 2024-06-24 15:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('strategy', '0007_useroutstrategy_income'),
    ]

    operations = [
        migrations.AlterField(
            model_name='strategy',
            name='max_deposit',
            field=models.DecimalField(blank=True, decimal_places=2, default=None, max_digits=30, null=True),
        ),
        migrations.AlterField(
            model_name='strategy',
            name='min_deposit',
            field=models.DecimalField(decimal_places=2, default=10, max_digits=30),
        ),
    ]
