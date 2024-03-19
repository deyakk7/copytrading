# Generated by Django 5.0.3 on 2024-03-19 20:03

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trader', '0003_alter_trader_nickname'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='trader',
            name='copiers_count',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='trader',
            name='followers_count',
            field=models.IntegerField(default=0),
        ),
        migrations.CreateModel(
            name='UsersFollowsTrader',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_of_following', models.DateTimeField(auto_now_add=True)),
                ('trader', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='followers', to='trader.trader')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='followed_traders', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('user', 'trader')},
            },
        ),
    ]