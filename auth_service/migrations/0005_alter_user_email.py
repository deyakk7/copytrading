# Generated by Django 5.0.3 on 2024-03-18 20:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auth_service', '0004_alter_user_email'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='email',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
