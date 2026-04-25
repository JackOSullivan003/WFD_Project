"""
URL configuration for main project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static

from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),

    path('manager/', views.manager_dashboard, name='manager_dashboard'),
    path('manager/items/', views.manager_items, name='manager_items'),
    path('manager/items/<int:pk>/edit/', views.manager_item_edit, name='manager_item_edit'),
    path('manager/items/<int:pk>/delete/', views.manager_item_delete, name='manager_item_delete'),
    path('manager/warehouses/', views.manager_warehouses, name='manager_warehouses'),
    path('manager/warehouses/<int:pk>/edit/', views.manager_warehouse_edit, name='manager_warehouse_edit'),
    path('manager/warehouses/<int:pk>/delete/', views.manager_warehouse_delete, name='manager_warehouse_delete'),


    path('clerk/', views.clerk_dashboard, name='clerk_dashboard'),
    path('warehouse-manager/', views.warehouse_manager_dashboard, name='warehouse_manager_dashboard'),
    path('worker/', views.worker_dashboard, name='worker_dashboard'),
    path('courier/', views.courier_dashboard, name='courier_dashboard'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
