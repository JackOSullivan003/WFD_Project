from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout as auth_logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required

from sports_logistics.models import User, ItemDefinition, Order, OrderItem, Warehouse, Stock, StockTransfer

import random
import string


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
def dashboard(request): #central dashboard router
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

def clerk_required(view_func):
    #decorater for clerk 
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_order_clerk():
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper
 
 
def generate_order_number():
    # generates a unique order number like ORD-A1B2C3
    while True:
        suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        number = f'ORD-{suffix}'
        if not Order.objects.filter(order_number=number).exists():
            return number
 
 
@login_required
@clerk_required
def clerk_dashboard(request):
    orders = Order.objects.filter(clerk=request.user).order_by('-created_at')
    return render(request, 'clerk/dashboard.html', {'orders': orders})
 
 
@login_required
@clerk_required
def clerk_create_order(request):
    if request.method == 'POST':
        organisation = request.POST.get('organisation', '').strip()
        delivery_address = request.POST.get('delivery_address', '').strip()
        delivery_date = request.POST.get('delivery_date')
        warehouse_id = request.POST.get('warehouse')
        delivery_fee = request.POST.get('delivery_fee', '0')
        notes = request.POST.get('notes', '').strip()
 
        # collect item rows from the form
        item_ids = request.POST.getlist('item_id')
        quantities = request.POST.getlist('quantity')
 
        if organisation and delivery_address and delivery_date and warehouse_id:
            warehouse = get_object_or_404(Warehouse, pk=warehouse_id)
 
            order = Order.objects.create(
                order_number=generate_order_number(),
                organisation=organisation,
                delivery_address=delivery_address,
                delivery_date=delivery_date,
                warehouse=warehouse,
                clerk=request.user,
                delivery_fee=delivery_fee,
                notes=notes,
                status=Order.STATUS_PENDING,
            )
 
            # create order items
            for item_id, quantity in zip(item_ids, quantities):
                try:
                    item = ItemDefinition.objects.get(pk=item_id)
                    qty = int(quantity)
                    if qty > 0:
                        OrderItem.objects.create(order=order, item=item, quantity=qty)
                except (ItemDefinition.DoesNotExist, ValueError):
                    pass
 
            order.recalculate_total()
            return redirect('clerk_dashboard')
 
    warehouses = Warehouse.objects.all()
    items = ItemDefinition.objects.all().order_by('name')
    return render(request, 'clerk/order.html', {
        'warehouses': warehouses,
        'items': items,
    })
 
@login_required 
@clerk_required
def clerk_edit_order(request, pk):
    order = get_object_or_404(Order, pk=pk)
    if request.method == 'POST':
        order.organisation = request.POST.get('organisation', '').strip()
        order.delivery_address = request.POST.get('delivery_address', '').strip()
        order.delivery_date = request.POST.get('delivery_date')
        order.delivery_fee = request.POST.get('delivery_fee', '0')
        order.notes = request.POST.get('notes', '').strip()
        order.warehouse = get_object_or_404(Warehouse, pk= request.POST.get('warehouse'))

        item_ids = request.POST.getlist('item_id')
        quantities = request.POST.getlist('quantity')

        order.order_items.all().delete()

        for item_id, quantity in zip(item_ids, quantities):
                try:
                    item = ItemDefinition.objects.get(pk=item_id)
                    qty = int(quantity)
                    if qty > 0:
                        OrderItem.objects.create(order=order, item=item, quantity=qty)
                except (ItemDefinition.DoesNotExist, ValueError):
                    pass
        order.save()
        order.recalculate_total()
        return redirect('clerk_dashboard')
    warehouses = Warehouse.objects.all()
    items = ItemDefinition.objects.all().order_by('name')
    order_items = [
        {
            "item_id": oi.item.pk,
            "quantity": oi.quantity,
        }
        for oi in order.order_items.all()
    ]

    return render(request, 'clerk/order.html', {
        'warehouses': warehouses, 
        'items': items,
        'order': order,
        'order_items': order_items,
    })



 
@login_required
@clerk_required
def clerk_cancel_order(request, pk):
    order = get_object_or_404(Order, pk=pk, clerk=request.user)
    if request.method == 'POST' and order.status == Order.STATUS_PENDING:
        order.status = Order.STATUS_CANCELLED
        order.save()
    return redirect('clerk_dashboard')


@login_required
def warehouse_manager_dashboard(request):
    if not request.user.is_warehouse_manager():
        return redirect('dashboard')
    return render(request, 'warehouse_manager/dashboard.html')

def warehouse_manager_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_warehouse_manager():
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper
 
 
def get_manager_warehouse(user):
    # returns the warehouse this manager is assigned to, or None
    try:
        return user.managed_warehouse
    except Exception:
        return None
 
 
@login_required
@warehouse_manager_required
def warehouse_manager_dashboard(request):
    warehouse = get_manager_warehouse(request.user)
 
    if warehouse is None:
        return render(request, 'warehouse_manager/dashboard.html', {'no_warehouse': True})
 
    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        action = request.POST.get('action')
        order = get_object_or_404(Order, pk=order_id, warehouse=warehouse)
 
        if action == 'accept' and order.status == Order.STATUS_PENDING:
            order.status = Order.STATUS_ACCEPTED
            order.save()
        elif action == 'reject' and order.status == Order.STATUS_PENDING:
            order.status = Order.STATUS_CANCELLED
            order.save()
 
        return redirect('warehouse_manager_dashboard')
 
    pending_orders = Order.objects.filter(
        warehouse=warehouse, status=Order.STATUS_PENDING
    ).order_by('delivery_date')
 
    active_orders = Order.objects.filter(
        warehouse=warehouse,
        status__in=[Order.STATUS_ACCEPTED, Order.STATUS_PACKAGING, Order.STATUS_READY]
    ).prefetch_related('order_items__item').order_by('delivery_date')
 
    return render(request, 'warehouse_manager/dashboard.html', {
        'warehouse': warehouse,
        'pending_orders': pending_orders,
        'active_orders': active_orders,
    })
 
 
@login_required
@warehouse_manager_required
def warehouse_manager_stock(request):
    warehouse = get_manager_warehouse(request.user)
 
    if warehouse is None:
        return redirect('warehouse_manager_dashboard')
 
    if request.method == 'POST':
        action = request.POST.get('action')
 
        if action == 'add':
            # add an item definition to this warehouse's stock
            item_id = request.POST.get('item_id')
            quantity = request.POST.get('quantity', 0)
            item = get_object_or_404(ItemDefinition, pk=item_id)
            stock, created = Stock.objects.get_or_create(
                warehouse=warehouse, item=item,
                defaults={'quantity': 0}
            )
            stock.quantity += int(quantity)
            stock.save()
 
        elif action == 'update':
            # update quantity of existing stock entry
            stock_id = request.POST.get('stock_id')
            quantity = request.POST.get('quantity', 0)
            stock = get_object_or_404(Stock, pk=stock_id, warehouse=warehouse)
            stock.quantity = int(quantity)
            stock.save()
 
        elif action == 'remove':
            stock_id = request.POST.get('stock_id')
            stock = get_object_or_404(Stock, pk=stock_id, warehouse=warehouse)
            stock.delete()
 
        return redirect('warehouse_manager_stock')
 
    current_stock = Stock.objects.filter(
        warehouse=warehouse
    ).select_related('item').order_by('item__name')
 
    # items not yet in this warehouse's stock
    stocked_item_ids = current_stock.values_list('item_id', flat=True)
    unstocked_items = ItemDefinition.objects.exclude(pk__in=stocked_item_ids).order_by('name')
 
    return render(request, 'warehouse_manager/stock.html', {
        'warehouse': warehouse,
        'current_stock': current_stock,
        'unstocked_items': unstocked_items,
    })
 
 
@login_required
@warehouse_manager_required
def warehouse_manager_transfers(request):
    warehouse = get_manager_warehouse(request.user)
 
    if warehouse is None:
        return redirect('warehouse_manager_dashboard')
 
    if request.method == 'POST':
        item_id = request.POST.get('item_id')
        to_warehouse_id = request.POST.get('to_warehouse')
        quantity = request.POST.get('quantity', 0)
 
        item = get_object_or_404(ItemDefinition, pk=item_id)
        to_warehouse = get_object_or_404(Warehouse, pk=to_warehouse_id)
 
        StockTransfer.objects.create(
            from_warehouse=warehouse,
            to_warehouse=to_warehouse,
            item=item,
            quantity=int(quantity),
            requested_by=request.user,
            status=StockTransfer.STATUS_REQUESTED,
        )
        return redirect('warehouse_manager_transfers')
 
    # transfers involving this warehouse
    outgoing = StockTransfer.objects.filter(
        from_warehouse=warehouse
    ).select_related('item', 'to_warehouse', 'courier').order_by('-created_at')
 
    incoming = StockTransfer.objects.filter(
        to_warehouse=warehouse
    ).select_related('item', 'from_warehouse', 'courier').order_by('-created_at')
 
    # stock this warehouse has available to transfer
    available_stock = Stock.objects.filter(
        warehouse=warehouse, quantity__gt=0
    ).select_related('item')
 
    other_warehouses = Warehouse.objects.exclude(pk=warehouse.pk)
 
    return render(request, 'warehouse_manager/transfers.html', {
        'warehouse': warehouse,
        'outgoing': outgoing,
        'incoming': incoming,
        'available_stock': available_stock,
        'other_warehouses': other_warehouses,
    })

@login_required
def worker_dashboard(request):
    if not request.user.is_warehouse_worker():
        return redirect('dashboard')
    return render(request, 'warehouse_worker/dashboard.html')

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from sports_logistics.models import Order, OrderItem, Stock


def warehouse_worker_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_warehouse_worker():
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


@login_required
@warehouse_worker_required
def worker_dashboard(request):
    # workers see accepted orders from all warehouses
    orders = Order.objects.filter(
        status__in=[Order.STATUS_ACCEPTED, Order.STATUS_PACKAGING]
    ).prefetch_related('order_items__item').select_related('warehouse').order_by('delivery_date')

    return render(request, 'warehouse_worker/dashboard.html', {'orders': orders})


@login_required
@warehouse_worker_required
def worker_order(request, pk):
    order = get_object_or_404(
        Order, pk=pk,
        status__in=[Order.STATUS_ACCEPTED, Order.STATUS_PACKAGING, Order.STATUS_READY]
    )

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'pack_item':
            item_id = request.POST.get('order_item_id')
            order_item = get_object_or_404(OrderItem, pk=item_id, order=order)

            if not order_item.packed:
                # deduct from stock
                try:
                    stock = Stock.objects.get(
                        warehouse=order.warehouse, item=order_item.item
                    )
                    stock.quantity = max(0, stock.quantity - order_item.quantity)
                    stock.save()
                except Stock.DoesNotExist:
                    pass

                order_item.packed = True
                order_item.save()

            # set order to packaging if not already
            if order.status == Order.STATUS_ACCEPTED:
                order.status = Order.STATUS_PACKAGING
                order.assigned_worker = request.user
                order.save()

            # check if all items are packed
            if not order.order_items.filter(packed=False).exists():
                order.status = Order.STATUS_READY
                order.save()

        elif action == 'unpack_item':
            # allow undoing a pack in case of mistake
            item_id = request.POST.get('order_item_id')
            order_item = get_object_or_404(OrderItem, pk=item_id, order=order)

            if order_item.packed and order.status != Order.STATUS_READY:
                # return stock
                try:
                    stock = Stock.objects.get(
                        warehouse=order.warehouse, item=order_item.item
                    )
                    stock.quantity += order_item.quantity
                    stock.save()
                except Stock.DoesNotExist:
                    pass

                order_item.packed = False
                order_item.save()

        return redirect('worker_order', pk=order.pk)

    items = order.order_items.select_related('item').all()
    all_packed = not items.filter(packed=False).exists()

    return render(request, 'warehouse_worker/order.html', {
        'order': order,
        'items': items,
        'all_packed': all_packed,
    })


@login_required
def courier_dashboard(request):
    if not request.user.is_courier():
        return redirect('dashboard')
    return render(request, 'courier/dashboard.html')

def courier_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_courier():
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper
 
 
@login_required
@courier_required
def courier_dashboard(request):
    # orders ready for collection that have no courier yet
    available_orders = Order.objects.filter(
        status=Order.STATUS_READY, assigned_courier=None
    ).select_related('warehouse').order_by('delivery_date')
 
    # this courier's active deliveries
    my_orders = Order.objects.filter(
        assigned_courier=request.user,
        status=Order.STATUS_ASSIGNED
    ).select_related('warehouse').order_by('delivery_date')
 
    # stock transfers available to claim
    available_transfers = StockTransfer.objects.filter(
        status=StockTransfer.STATUS_REQUESTED, courier=None
    ).select_related('item', 'from_warehouse', 'to_warehouse').order_by('-created_at')
 
    # this courier's active transfers
    my_transfers = StockTransfer.objects.filter(
        courier=request.user,
        status__in=[StockTransfer.STATUS_ASSIGNED, StockTransfer.STATUS_IN_TRANSIT]
    ).select_related('item', 'from_warehouse', 'to_warehouse').order_by('-created_at')
 
    return render(request, 'courier/dashboard.html', {
        'available_orders': available_orders,
        'my_orders': my_orders,
        'available_transfers': available_transfers,
        'my_transfers': my_transfers,
    })
 
 
@login_required
@courier_required
def courier_claim_order(request, pk):
    order = get_object_or_404(Order, pk=pk, status=Order.STATUS_READY, assigned_courier=None)
    if request.method == 'POST':
        order.assigned_courier = request.user
        order.status = Order.STATUS_ASSIGNED
        order.save()
    return redirect('courier_dashboard')
 
 
@login_required
@courier_required
def courier_deliver_order(request, pk):
    order = get_object_or_404(Order, pk=pk, assigned_courier=request.user, status=Order.STATUS_ASSIGNED)
    if request.method == 'POST':
        order.status = Order.STATUS_DELIVERED
        order.save()
    return redirect('courier_dashboard')
 
 
@login_required
@courier_required
def courier_claim_transfer(request, pk):
    transfer = get_object_or_404(StockTransfer, pk=pk, status=StockTransfer.STATUS_REQUESTED, courier=None)
    if request.method == 'POST':
        transfer.courier = request.user
        transfer.status = StockTransfer.STATUS_ASSIGNED
        transfer.save()
    return redirect('courier_dashboard')
 
 
@login_required
@courier_required
def courier_complete_transfer(request, pk):
    transfer = get_object_or_404(
        StockTransfer, pk=pk, courier=request.user,
        status__in=[StockTransfer.STATUS_ASSIGNED, StockTransfer.STATUS_IN_TRANSIT]
    )
    if request.method == 'POST':
        action = request.POST.get('action')
 
        if action == 'in_transit':
            transfer.status = StockTransfer.STATUS_IN_TRANSIT
            transfer.save()
 
        elif action == 'complete':
            transfer.status = StockTransfer.STATUS_COMPLETED
            transfer.save()
 
            # deduct from source warehouse
            try:
                source_stock = Stock.objects.get(
                    warehouse=transfer.from_warehouse, item=transfer.item
                )
                source_stock.quantity = max(0, source_stock.quantity - transfer.quantity)
                source_stock.save()
            except Stock.DoesNotExist:
                pass
 
            # add to destination warehouse
            dest_stock, created = Stock.objects.get_or_create(
                warehouse=transfer.to_warehouse, item=transfer.item,
                defaults={'quantity': 0}
            )
            dest_stock.quantity += transfer.quantity
            dest_stock.save()
 
    return redirect('courier_dashboard')