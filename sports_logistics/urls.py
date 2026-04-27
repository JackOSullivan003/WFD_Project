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
    path('clerk/orders/create/', views.clerk_create_order, name='clerk_create_order'),
    path('clerk/orders/<int:pk>/edit/', views.clerk_edit_order, name='clerk_edit_order'),
    path('clerk/orders/<int:pk>/cancel/', views.clerk_cancel_order, name='clerk_cancel_order'),


    path('warehouse-manager/', views.warehouse_manager_dashboard, name='warehouse_manager_dashboard'),
    path('warehouse-manager/stock/', views.warehouse_manager_stock, name='warehouse_manager_stock'),
    path('warehouse-manager/transfers/', views.warehouse_manager_transfers, name='warehouse_manager_transfers'),


    path('worker/', views.worker_dashboard, name='worker_dashboard'),
    path('worker/orders/<int:pk>/', views.worker_order, name='worker_order'),

    path('courier/', views.courier_dashboard, name='courier_dashboard'),
    path('courier/orders/<int:pk>/claim/', views.courier_claim_order, name='courier_claim_order'),
    path('courier/orders/<int:pk>/deliver/', views.courier_deliver_order, name='courier_deliver_order'),
    path('courier/transfers/<int:pk>/claim/', views.courier_claim_transfer, name='courier_claim_transfer'),
    path('courier/transfers/<int:pk>/complete/', views.courier_complete_transfer, name='courier_complete_transfer'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
