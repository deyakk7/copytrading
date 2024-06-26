# Generated by Django 5.0.3 on 2024-04-14 09:44

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('strategy', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CryptoPriceHistory24h',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=30)),
                ('highest_price', models.DecimalField(decimal_places=7, default=0, max_digits=30)),
                ('lowest_price', models.DecimalField(decimal_places=7, default=0, max_digits=30)),
            ],
        ),
        migrations.CreateModel(
            name='Crypto',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=30)),
                ('total_value', models.DecimalField(decimal_places=2, max_digits=5, validators=[django.core.validators.MaxValueValidator(100), django.core.validators.MinValueValidator(0)])),
                ('side', models.CharField(blank=True, choices=[('short', 'short'), ('long', 'long')], default='long', max_length=10, null=True)),
                ('strategy', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='crypto', to='strategy.strategy')),
            ],
        ),
    ]
