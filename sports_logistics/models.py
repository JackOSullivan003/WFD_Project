from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_COMPANY_MANAGER = 'company_manager'
    ROLE_ORDER_CLERK = 'order_clerk'
    ROLE_WAREHOUSE_MANAGER = 'warehouse_manager'
    ROLE_WAREHOUSE_WORKER = 'warehouse_worker'
    ROLE_COURIER = 'courier'

    ROLE_CHOICES = [
        (ROLE_COMPANY_MANAGER, 'Company Manager'),
        (ROLE_ORDER_CLERK, 'Order Clerk'),
        (ROLE_WAREHOUSE_MANAGER, 'Warehouse Manager'),
        (ROLE_WAREHOUSE_WORKER, 'Warehouse Worker'),
        (ROLE_COURIER, 'Courier'),
    ]

    role = models.CharField(max_length=30, choices=ROLE_CHOICES, default=ROLE_ORDER_CLERK)
    phone = models.CharField(max_length=20, blank=True)

    def is_company_manager(self):
        return self.role == self.ROLE_COMPANY_MANAGER or self.is_superuser

    def is_order_clerk(self):
        return self.role == self.ROLE_ORDER_CLERK

    def is_warehouse_manager(self):
        return self.role == self.ROLE_WAREHOUSE_MANAGER

    def is_warehouse_worker(self):
        return self.role == self.ROLE_WAREHOUSE_WORKER

    def is_courier(self):
        return self.role == self.ROLE_COURIER

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


class ItemDefinition(models.Model):
    # items the company sells, defined by the company manager
    name = models.CharField(max_length=200)
    image = models.ImageField(upload_to='items/', blank=True, null=True)
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_items')

    def __str__(self):
        return self.name


class Warehouse(models.Model):
    # created by company manager, assigned a warehouse manager
    name = models.CharField(max_length=150)
    location = models.CharField(max_length=200)
    manager = models.OneToOneField(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='managed_warehouse',
        limit_choices_to={'role': User.ROLE_WAREHOUSE_MANAGER}
    )

    def __str__(self):
        return f"{self.name} ({self.location})"


class Stock(models.Model):
    # tracks how many of an item a warehouse currently holds
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='stock')
    item = models.ForeignKey(ItemDefinition, on_delete=models.CASCADE, related_name='stock')
    quantity = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('warehouse', 'item')

    def __str__(self):
        return f"{self.item.name} x{self.quantity} @ {self.warehouse.name}"


class Order(models.Model):
    STATUS_PENDING = 'pending'           # created by clerk, waiting for warehouse
    STATUS_ACCEPTED = 'accepted'         # warehouse manager has accepted it
    STATUS_PACKAGING = 'packaging'       # warehouse worker is packing it
    STATUS_READY = 'ready'               # fully packed, waiting for courier
    STATUS_ASSIGNED = 'assigned'         # courier has claimed it
    STATUS_DELIVERED = 'delivered'
    STATUS_CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_ACCEPTED, 'Accepted'),
        (STATUS_PACKAGING, 'Packaging'),
        (STATUS_READY, 'Ready for Collection'),
        (STATUS_ASSIGNED, 'Assigned to Courier'),
        (STATUS_DELIVERED, 'Delivered'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    order_number = models.CharField(max_length=20, unique=True)
    organisation = models.CharField(max_length=200)
    delivery_address = models.TextField()
    delivery_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)

    warehouse = models.ForeignKey(Warehouse, on_delete=models.SET_NULL, null=True, related_name='orders')
    clerk = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name='created_orders',
        limit_choices_to={'role': User.ROLE_ORDER_CLERK}
    )
    assigned_worker = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_orders',
        limit_choices_to={'role': User.ROLE_WAREHOUSE_WORKER}
    )
    assigned_courier = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='deliveries',
        limit_choices_to={'role': User.ROLE_COURIER}
    )

    delivery_fee = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    total_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order {self.order_number} - {self.organisation}"

    def recalculate_total(self):
        # sums sale price * quantity for all items on the order
        total = sum(oi.item.sale_price * oi.quantity for oi in self.order_items.all())
        self.total_charge = total
        self.save()


class OrderItem(models.Model):
    # individual line items on an order
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_items')
    item = models.ForeignKey(ItemDefinition, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    packed = models.BooleanField(default=False)  # worker marks this when item is packaged

    def __str__(self):
        return f"{self.quantity}x {self.item.name} (Order {self.order.order_number})"


class StockTransfer(models.Model):
    # a request to move stock from one warehouse to another
    STATUS_REQUESTED = 'requested'
    STATUS_ASSIGNED = 'assigned'
    STATUS_IN_TRANSIT = 'in_transit'
    STATUS_COMPLETED = 'completed'
    STATUS_CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (STATUS_REQUESTED, 'Requested'),
        (STATUS_ASSIGNED, 'Courier Assigned'),
        (STATUS_IN_TRANSIT, 'In Transit'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    from_warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='transfers_out')
    to_warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='transfers_in')
    item = models.ForeignKey(ItemDefinition, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_REQUESTED)
    requested_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name='requested_transfers',
        limit_choices_to={'role': User.ROLE_WAREHOUSE_MANAGER}
    )
    courier = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='transfer_runs',
        limit_choices_to={'role': User.ROLE_COURIER}
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Transfer {self.item.name} x{self.quantity}: {self.from_warehouse.name} to {self.to_warehouse.name}"