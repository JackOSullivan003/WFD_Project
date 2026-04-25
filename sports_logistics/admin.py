from django.contrib import admin

# Register your models here.
from .models import User,Warehouse, ItemDefinition, Stock

admin.site.register(User)
admin.site.register(Warehouse)
admin.site.register(ItemDefinition)
admin.site.register(Stock)

