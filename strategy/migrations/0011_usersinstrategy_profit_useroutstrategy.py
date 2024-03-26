# Generated by Django 5.0.3 on 2024-03-26 18:02

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('strategy', '0010_strategyprofithistory'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='usersinstrategy',
            name='profit',
            field=models.DecimalField(decimal_places=7, default=0, max_digits=30),
        ),
        migrations.CreateModel(
            name='UserOutStrategy',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value', models.DecimalField(decimal_places=7, default=0, max_digits=30)),
                ('date_of_adding', models.DateTimeField(default=django.utils.timezone.now)),
                ('date_of_out', models.DateTimeField(auto_now_add=True)),
                ('profit', models.DecimalField(decimal_places=7, default=0, max_digits=30)),
                ('strategy', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='out_users', to='strategy.strategy')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='out_strategies', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
