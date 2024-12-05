# api/urls.py
from django.urls import path
from .views import ProductListView
from .views import fetch_image_view

urlpatterns = [
    path('products/', ProductListView.as_view(), name='product-list'),
    path('fetch-image/', fetch_image_view, name='fetch_image'),
]
