"""
URL configuration for myproject project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path,include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import render
from django.urls import path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from . import views
from .views import custom_404

handler404 = custom_404

# Set up the schema view for Swagger UI
schema_view = get_schema_view(
   openapi.Info(
      title="Ramze Pharmacy API",
      default_version='v1',
      description="API for managing products in the Ramze Pharmacy",
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="contact@ramzepharmacy.com"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

# Create a simple view for the root URL
def home(request):
    return render(request, 'home.html')  # Render home.html template

urlpatterns = [
    path('', home, name='home'),  # Root URL pattern
    path('ui/', views.index, name='index'),  # Serve the frontend HTML at the root
    path('admin/', admin.site.urls),
    path('dashboard/', include('dashboard.urls')),# Include dashboard URLs
    path('api/', include('api.urls')),  # Include the API URLs
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
]
# Add Django Debug Toolbar URLs only in DEBUG mode
if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        path('__debug__/', include(debug_toolbar.urls)),
    ]
# if settings.DEBUG:
#     urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)




