from django.db import models


class Trader(models.Model):
    nickname = models.CharField(max_length=50)
    about = models.CharField(max_length=500, blank=True)
    date_of_registration = models.DateTimeField(auto_now_add=True)
    photo = models.ImageField(upload_to='trader_photos', blank=True)

    def __str__(self):
        return f"{self.nickname}"
