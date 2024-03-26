from django.contrib import admin

from crypto.models import Crypto, CryptoInUser

admin.site.register(Crypto)
admin.site.register(CryptoInUser)
