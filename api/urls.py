# api/urls.py
from django.urls import path
from . import views
from .views import ProductListView
from .views import ProductListByCompanyView
from .views import ProductListByGroupView

urlpatterns = [
    path('', views.home, name='home'),  # Default route for api
    # path('product/', ProductListView.as_view(), name='product-list'),
    path('product/allproducts/', ProductListView.as_view(), name='product-list'),  # List all products (alternative URL)
    # path('product/<int:product_id>/', ProductDetailView.as_view(), name='product-detail'),  # Get product by ID
    # path('allproducts/company/<int:pk>/', ProductListByCompanyView.as_view(), name='product-list-by-company'),
    path('productsByCompany_id/<int:company_id>/', ProductListByCompanyView.as_view(), name='product-list-by-company'),
    path('productsByGroup_id/<int:group_id>/', ProductListByGroupView.as_view(), name='product-list-by-group'),
]
