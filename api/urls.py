# api/urls.py
from django.urls import path

from api.utils import health_check
from . import views
from .views import ProductListView,ProductListByCompanyView,ProductListByGroupView,ProductDetailView
from .views import ProductSearchView,CategoryView,LoginView,RegisterView,UserProfileView


urlpatterns = [
    #GET
    path('', views.home, name='home'),  # Default route for api
    path('health/', health_check, name='health_check'),
    path('product/allProducts/', ProductListView.as_view(), name='product-list'),  # List all products (alternative URL)
    path('product/<int:product_id>/', ProductDetailView.as_view(), name='product-detail'),  # Get product by ID
    path('productsByCompany_id/<int:company_id>/', ProductListByCompanyView.as_view(), name='product-list-by-company'),
    path('productsByGroup_id/<int:group_id>/', ProductListByGroupView.as_view(), name='product-list-by-group'),
    path('categories/', CategoryView.as_view(), name='category-list'),
    path('products/search/', ProductSearchView.as_view(), name='product-search'),
    path('me/', UserProfileView.as_view(), name='user-profile'),
    # Post
    # path('create-sale/', CreateSaleView.as_view(), name='create-sale'),
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
]




