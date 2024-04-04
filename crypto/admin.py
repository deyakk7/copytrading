from django.contrib import admin

from crypto.models import Crypto, CryptoInUser, CryptoPriceHistory24h

admin.site.register(Crypto)
admin.site.register(CryptoInUser)
admin.site.register(CryptoPriceHistory24h)
