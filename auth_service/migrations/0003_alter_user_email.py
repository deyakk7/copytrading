# Generated by Django 5.0.3 on 2024-03-18 19:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auth_service', '0002_user_ip'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='email',
            field=models.EmailField(blank=True, max_length=254, null=True, unique=True),
        ),
    ]
