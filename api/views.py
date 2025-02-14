# # api/views.py

from rest_framework.pagination import PageNumberPagination
from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import ProductSerializer
from django.shortcuts import render
from django.db import connection
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.core.cache import cache
import json
from .models import Product
from rest_framework import status

def home(request):
    return render(request, 'api/api_list.html')

class ProductListView(APIView):
    def get(self, request):
        # Get the page number from the request
        page_number = request.query_params.get('page', 1)

        # Generate a unique cache key for this page
        cache_key = f'product_list_page_{page_number}'
        # print("Cache key:", cache_key)  # Debugging

        # Check if the paginated data is cached
        cached_data = cache.get(cache_key)
        if cached_data:
            # print("Serving from cache:", cached_data)  # Debugging
            return Response(cached_data)

        # Define the raw SQL query
        query = """
            SELECT 
    p.product_id,
    p.product_code,
    p.product_name_ar,
    p.product_name_en,
    p.sell_price,
    p.product_image_url,
    (
        SELECT 
            c.company_id,
            c.co_name_en,
            c.co_name_ar
        FOR JSON PATH, WITHOUT_ARRAY_WRAPPER
    ) AS company,
    (
        SELECT 
            pg.group_id,
            pg.group_name_en,
            pg.group_name_ar
        FOR JSON PATH, WITHOUT_ARRAY_WRAPPER
    ) AS product_group
FROM 
    Products p
LEFT JOIN 
    Product_groups pg ON p.group_id = pg.group_id
LEFT JOIN 
    Companys c ON p.company_id = c.company_id
        """

        # Execute the raw SQL query
        with connection.cursor() as cursor:
            cursor.execute(query)
            columns = [col[0] for col in cursor.description]  # Get column names
            rows = cursor.fetchall()

        # Convert the rows into a list of dictionaries
        products = []
        for row in rows:
            product = dict(zip(columns, row))
            # Parse the nested JSON fields
            product['company'] = json.loads(product['company'])
            product['product_group'] = json.loads(product['product_group'])
            products.append(product)
        # print("Raw data from database:", products)  # Debugging

        # Set up pagination
        paginator = PageNumberPagination()
        paginator.page_size = 20
        result_page = paginator.paginate_queryset(products, request)

        # Build the response data
        response_data = {
            "count": paginator.page.paginator.count,
            "next": paginator.get_next_link(),
            "previous": paginator.get_previous_link(),
            "results": result_page,
        }
        # print("Response data before caching:", response_data)  # Debugging

        # Cache the entire response
        cache.set(cache_key, response_data, timeout=60 * 15)  # Cache for 15 minutes

        # Return the response
        return Response(response_data)

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

class ProductDetailView(APIView):
    def get(self, request, product_id):
        try:
            product = Product.objects.get(product_id=product_id)
            serializer = ProductSerializer(product)
            return Response(serializer.data)
        except Product.DoesNotExist:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)