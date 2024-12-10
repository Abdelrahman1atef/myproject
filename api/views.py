# # api/views.py

from rest_framework.pagination import PageNumberPagination
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Product
from .serializers import ProductSerializer

class ProductListView(APIView):
    def get(self, request):
        # Query all products from the database
        products = Product.objects.all()

        # Set up pagination
        paginator = PageNumberPagination()
        paginator.page_size = 20  # Set the page size to 10 items per page
        result_page = paginator.paginate_queryset(products, request)

        # Serialize the data
        serializer = ProductSerializer(result_page, many=True)

        # Return paginated data as a JSON response
        return paginator.get_paginated_response(serializer.data)

class ProductListByCompanyView(APIView):
    def get(self, request, company_id):
        # Query products by company_id
        products = Product.objects.filter(company_id=company_id)

        # Set up pagination
        paginator = PageNumberPagination()
        paginator.page_size = 20
        result_page = paginator.paginate_queryset(products, request)

        # Serialize the data
        serializer = ProductSerializer(result_page, many=True)

        # Return paginated data as a JSON response
        return paginator.get_paginated_response(serializer.data)

class ProductListByGroupView(APIView):
    def get(self, request, group_id):
        # Query products by group_id
        products = Product.objects.filter(group_id=group_id)

        # Set up pagination
        paginator = PageNumberPagination()
        paginator.page_size = 20
        result_page = paginator.paginate_queryset(products, request)

        # Serialize the data
        serializer = ProductSerializer(result_page, many=True)

        # Return paginated data as a JSON response
        return paginator.get_paginated_response(serializer.data)
