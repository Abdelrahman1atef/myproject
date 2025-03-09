# api/urls.py
from django.urls import path
from . import views
from .views import ProductListView,ProductListByCompanyView,ProductListByGroupView,ProductDetailView
from .views import CreateSaleView,ProductSearchView

urlpatterns = [
    path('', views.home, name='home'),  # Default route for api
    path('product/allProducts/', ProductListView.as_view(), name='product-list'),  # List all products (alternative URL)
    path('product/<int:product_id>/', ProductDetailView.as_view(), name='product-detail'),  # Get product by ID
    path('productsByCompany_id/<int:company_id>/', ProductListByCompanyView.as_view(), name='product-list-by-company'),
    path('productsByGroup_id/<int:group_id>/', ProductListByGroupView.as_view(), name='product-list-by-group'),
    path('products/search/', ProductSearchView.as_view(), name='product-search'),
    # Create Sale
    path('create-sale/', CreateSaleView.as_view(), name='create-sale'),
]
