# api/urls.py
from django.urls import path
from . import views
from .views import ProductListView
from .views import ProductListByCompanyView
from .views import ProductListByGroupView

urlpatterns = [
    path('', views.home, name='home'),  # Default route for api
    path('allproducts/', ProductListView.as_view(), name='product-list'),
    path('productsByCompany_id/<int:company_id>/', ProductListByCompanyView.as_view(), name='product-list-by-company'),
    path('productsByGroup_id/<int:group_id>/', ProductListByGroupView.as_view(), name='product-list-by-group'),
]
