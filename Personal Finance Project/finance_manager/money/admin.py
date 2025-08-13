from django.contrib import admin

from .models import Transaction, Category, Account, Budget
admin.site.register([Transaction, Category, Account, Budget])
