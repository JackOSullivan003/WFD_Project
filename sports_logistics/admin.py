from django.contrib import admin

# Register your models here.
from .models import User,Warehouse,Category,Parcel

admin.site.register(User)
admin.site.register(Warehouse)
admin.site.register(Category)
admin.site.register(Parcel)
