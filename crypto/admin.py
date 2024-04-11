from django.contrib import admin

from crypto.models import Crypto, CryptoPriceHistory24h

admin.site.register(Crypto)
admin.site.register(CryptoPriceHistory24h)
