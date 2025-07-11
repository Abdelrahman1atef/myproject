# api/urls.py
from django.urls import path

from api.utils import health_check
from . import views
from .views import ProductListView,ProductListByCompanyView,ProductListByGroupView,ProductDetailView
from .views import ProductSearchView,CategoryView,LoginView,RegisterView,UserProfileView,CreateOrderView
from .views import DeviceTokenView,AdminOrderListView,OrderStatusUpdateAPIView, CustomerOrderListView
from .views import DeviceTokenRegisterView

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
    path('admin/orders/', AdminOrderListView.as_view(), name='admin-order-list'),
    path('customer/orders/', CustomerOrderListView.as_view(), name='customer-orders'),
    path('products/best-sellers/', views.BestSellersView.as_view(), name='best-sellers'),
    path('products/see-our-products/', views.SeeOurProductsView.as_view(), name='see-our-products'),
    path('admin/users/', views.AllUsersView.as_view(), name='all-users'),
    path('admin/users/<int:user_id>/', views.UserDetailView.as_view(), name='user-detail'),
    path('admin/dashboard/', views.DashboardView.as_view(), name='admin-dashboard'),
    # Post
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('create-order/', CreateOrderView.as_view(), name='create_order'),
    path('save-device-token/', DeviceTokenView.as_view(), name='save-device-token'),

    # Patch
    path('admin/orders/status/<int:pk>/', OrderStatusUpdateAPIView.as_view(), name='order-status-update'),

    # New URL pattern for FCM token registration
    path('device/fcm-token/', DeviceTokenRegisterView.as_view(), name='fcm-token'),
]




