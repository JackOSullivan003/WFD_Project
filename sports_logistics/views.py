from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout as auth_logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required

from sports_logistics.models import ItemDefinition, Warehouse, Order, User

# Create your views here.
def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        login(request, form.get_user())
        return redirect('dashboard')

    return render(request, 'login.html', {'form': form})


def logout_view(request):
    auth_logout(request)
    return redirect('login')

@login_required
def dashboard(request):
    user = request.user
 
    if user.is_company_manager():
        return redirect('manager_dashboard')
    elif user.is_order_clerk():
        return redirect('clerk_dashboard')
    elif user.is_warehouse_manager():
        return redirect('warehouse_manager_dashboard')
    elif user.is_warehouse_worker():
        return redirect('worker_dashboard')
    elif user.is_courier():
        return redirect('courier_dashboard')
 
    return render(request, 'login.html', {'form': AuthenticationForm()})


@login_required
def manager_dashboard(request):
    if not request.user.is_company_manager():
        return redirect('dashboard')
    return render(request, 'manager/dashboard.html')

def manager_required(view_func):
    # decorator to restrict views to company managers only
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_company_manager():
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper

@login_required
@manager_required
def manager_dashboard(request):
    context = {
        'total_items': ItemDefinition.objects.count(),
        'total_warehouses': Warehouse.objects.count(),
        'total_orders': Order.objects.count(),
        'pending_orders': Order.objects.filter(status=Order.STATUS_PENDING).count(),
        'recent_orders': Order.objects.order_by('-created_at')[:5],
    }
    return render(request, 'manager/dashboard.html', context)
 
 
@login_required
@manager_required
def manager_items(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        purchase_price = request.POST.get('purchase_price')
        sale_price = request.POST.get('sale_price')
        image = request.FILES.get('image')
 
        if name and purchase_price and sale_price:
            ItemDefinition.objects.create(
                name=name,
                purchase_price=purchase_price,
                sale_price=sale_price,
                image=image,
                created_by=request.user,
            )
        return redirect('manager_items')
 
    items = ItemDefinition.objects.all().order_by('name')
    return render(request, 'manager/items.html', {'items': items})
 

@login_required
@manager_required
def manager_item_edit(request, pk):
    item = get_object_or_404(ItemDefinition, pk=pk)
    if request.method == 'POST':
        item.name = request.POST.get('name', '').strip()
        item.purchase_price = request.POST.get('purchase_price')
        item.sale_price = request.POST.get('sale_price')
        if request.FILES.get('image'):
            item.image = request.FILES.get('image')
        item.save()
        return redirect('manager_items')
 
    items = ItemDefinition.objects.all().order_by('name')
    return render(request, 'manager/items.html', {'items': items, 'editing': item})
 
 
@login_required
@manager_required
def manager_item_delete(request, pk):
    item = get_object_or_404(ItemDefinition, pk=pk)
    if request.method == 'POST':
        item.delete()
    return redirect('manager_items')

@login_required
@manager_required
def manager_warehouses(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        location = request.POST.get('location', '').strip()
        manager_id = request.POST.get('manager')
 
        if name and location:
            warehouse = Warehouse.objects.create(name=name, location=location)
            if manager_id:
                try:
                    manager = User.objects.get(pk=manager_id, role=User.ROLE_WAREHOUSE_MANAGER)
                    warehouse.manager = manager
                    warehouse.save()
                except User.DoesNotExist:
                    pass
        return redirect('manager_warehouses')
 
    warehouses = Warehouse.objects.select_related('manager').all()
    available_managers = User.objects.filter(
        role=User.ROLE_WAREHOUSE_MANAGER,
        managed_warehouse__isnull=True  # only unassigned managers
    )
    return render(request, 'manager/warehouses.html', {
        'warehouses': warehouses,
        'available_managers': available_managers,
    })

@login_required
@manager_required
def manager_warehouse_edit(request, pk):
    warehouse = get_object_or_404(Warehouse, pk=pk)
    if request.method == 'POST':
        warehouse.name = request.POST.get('name', '').strip()
        warehouse.location = request.POST.get('location', '').strip()
        manager_id = request.POST.get('manager')
        if manager_id:
            try:
                warehouse.manager = User.objects.get(pk=manager_id, role=User.ROLE_WAREHOUSE_MANAGER)
            except User.DoesNotExist:
                warehouse.manager = None
        else:
            warehouse.manager = None
        warehouse.save()
        return redirect('manager_warehouses')
 
    warehouses = Warehouse.objects.select_related('manager').all()
    all_managers = User.objects.filter(role=User.ROLE_WAREHOUSE_MANAGER)
    return render(request, 'manager/warehouses.html', {
        'warehouses': warehouses,
        'all_managers': all_managers,
        'editing': warehouse,
    })
 
 
@login_required
@manager_required
def manager_warehouse_delete(request, pk):
    warehouse = get_object_or_404(Warehouse, pk=pk)
    if request.method == 'POST':
        warehouse.delete()
    return redirect('manager_warehouses')



@login_required
def clerk_dashboard(request):
    if not request.user.is_order_clerk():
        return redirect('dashboard')
    return render(request, 'clerk/dashboard.html')


@login_required
def warehouse_manager_dashboard(request):
    if not request.user.is_warehouse_manager():
        return redirect('dashboard')
    return render(request, 'warehouse_manager/dashboard.html')


@login_required
def worker_dashboard(request):
    if not request.user.is_warehouse_worker():
        return redirect('dashboard')
    return render(request, 'warehouse_worker/dashboard.html')


@login_required
def courier_dashboard(request):
    if not request.user.is_courier():
        return redirect('dashboard')
    return render(request, 'courier/dashboard.html')