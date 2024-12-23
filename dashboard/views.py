from django.shortcuts import render
from django.http import HttpResponse
from .models import Product

def home(request):
    return HttpResponse("Welcome to the Admin Panel!")



def product_list(request):
    products = Product.objects.all()
    return render(request, 'dashboard/product_list.html', {'products': products})

