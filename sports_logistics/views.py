from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.utils import timezone

from .models import User, Parcel, Warehouse

# Create your views here.
def index(request):
    return redirect('login')

def login(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            # Redirect to a success page.
        else:
            # Return an 'invalid login' error message
            return render(request, 'main/login.html')
 
 
def logout(request):
    return redirect('login')
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required


def login_view(request):
    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        login(request, form.get_user())
        return redirect('dashboard')

    return render(request, 'login.html', {'form': form})


def logout_view(request):
    logout(request)
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