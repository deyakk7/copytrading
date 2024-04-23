from django.contrib import admin

from transaction.models import TransactionClose, TransactionOpen

admin.site.register(TransactionClose)
admin.site.register(TransactionOpen)
