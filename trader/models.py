from django.db import models


class Trader(models.Model):
    nickname = models.CharField(max_length=50)
    email = models.CharField(max_length=100, unique=True)
    password = models.CharField(max_length=300)
    date_of_registration = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nickname}"
