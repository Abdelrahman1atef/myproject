# api/urls.py
from django.urls import path
from . import views
from .views import ProductListView,ProductListByCompanyView,ProductListByGroupView,ProductDetailView
from .views import CreateSaleView,ProductSearchView,CategoryView

urlpatterns = [
    #GET
    path('', views.home, name='home'),  # Default route for api
    path('product/allProducts/', ProductListView.as_view(), name='product-list'),  # List all products (alternative URL)
    path('product/<int:product_id>/', ProductDetailView.as_view(), name='product-detail'),  # Get product by ID
    path('productsByCompany_id/<int:company_id>/', ProductListByCompanyView.as_view(), name='product-list-by-company'),
    path('productsByGroup_id/<int:group_id>/', ProductListByGroupView.as_view(), name='product-list-by-group'),
    path('categories/', CategoryView.as_view(), name='category-list'),
    path('products/search/', ProductSearchView.as_view(), name='product-search'),
    # Post
    path('create-sale/', CreateSaleView.as_view(), name='create-sale'),
]
