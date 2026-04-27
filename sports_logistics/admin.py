from django.contrib import admin

# Register your models here.
from .models import User, Order, OrderItem, Warehouse, ItemDefinition, Stock

admin.site.register(User)
admin.site.register(Order)
admin.site.register(Warehouse)
admin.site.register(ItemDefinition)
admin.site.register(Stock)


