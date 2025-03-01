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
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin


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
                ) AS product_group,
                ISNULL(
                    (SELECT CAST(SUM(pa.amount) AS INT) 
                     FROM Product_Amount pa
                     WHERE pa.product_id = p.product_id), 
                    0
                ) AS amount -- Replace NULL with 0
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
        page_number = request.query_params.get('page', 1)
        cache_key = f'product_list_company_{company_id}_page_{page_number}'
        cached_data = cache.get(cache_key)

        if cached_data:
            return Response(cached_data)
        query = f"""
    SELECT 
        p.product_id,
        p.product_code,
        p.product_name_ar,
        p.product_name_en,
        p.sell_price,
        p.product_image_url,

        -- Ensure company details are retrieved correctly
        JSON_QUERY((
            SELECT 
                c.company_id,
                c.co_name_en,
                c.co_name_ar
            FROM Companys c
            WHERE c.company_id = p.company_id
            FOR JSON PATH, WITHOUT_ARRAY_WRAPPER
        )) AS company,

        -- Ensure product group details are retrieved correctly
        JSON_QUERY((
            SELECT 
                pg.group_id,
                pg.group_name_en,
                pg.group_name_ar
            FROM Product_groups pg
            WHERE pg.group_id = p.group_id
            FOR JSON PATH, WITHOUT_ARRAY_WRAPPER
        )) AS product_group,

        -- Correctly calculate amount, replacing NULL with 0
        ISNULL((
            SELECT CAST(SUM(pa.amount) AS INT) 
            FROM Product_Amount pa 
            WHERE pa.product_id = p.product_id
        ), 0) AS amount

    FROM Products p
    WHERE p.company_id = {company_id}
"""

        with connection.cursor() as cursor:
            cursor.execute(query)
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()

        products = []
        for row in rows:
            product = dict(zip(columns, row))
            product['company'] = json.loads(product['company']) if product['company'] else None
            product['product_group'] = json.loads(product['product_group']) if product['product_group'] else None
            products.append(product)

        paginator = PageNumberPagination()
        paginator.page_size = 20
        result_page = paginator.paginate_queryset(products, request)

        response_data = {
            "count": paginator.page.paginator.count,
            "next": paginator.get_next_link(),
            "previous": paginator.get_previous_link(),
            "results": result_page,
        }

        cache.set(cache_key, response_data, timeout=60 * 15)
        return Response(response_data)


class ProductListByGroupView(APIView):
    def get(self, request, group_id):
        page_number = request.query_params.get('page', 1)
        cache_key = f'product_list_group_{group_id}_page_{page_number}'
        cached_data = cache.get(cache_key)

        if cached_data:
            return Response(cached_data)

        query = f"""
            SELECT 
                p.product_id,
                p.product_code,
                p.product_name_ar,
                p.product_name_en,
                p.sell_price,
                p.product_image_url,

                -- Get company details
                JSON_QUERY((
                    SELECT 
                        c.company_id,
                        c.co_name_en,
                        c.co_name_ar
                    FROM Companys c
                    WHERE c.company_id = p.company_id
                    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER
                )) AS company,

                -- Get product group details
                JSON_QUERY((
                    SELECT 
                        pg.group_id,
                        pg.group_name_en,
                        pg.group_name_ar
                    FROM Product_groups pg
                    WHERE pg.group_id = p.group_id
                    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER
                )) AS product_group,

                -- Calculate amount, replace NULL with 0
                ISNULL((
                    SELECT CAST(SUM(pa.amount) AS INT) 
                    FROM Product_Amount pa 
                    WHERE pa.product_id = p.product_id
                ), 0) AS amount

            FROM Products p
            WHERE p.group_id = {group_id}
        """

        with connection.cursor() as cursor:
            cursor.execute(query)
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()

        products = []
        for row in rows:
            product = dict(zip(columns, row))
            product['company'] = json.loads(product['company']) if product['company'] else None
            product['product_group'] = json.loads(product['product_group']) if product['product_group'] else None
            products.append(product)

        paginator = PageNumberPagination()
        paginator.page_size = 20
        result_page = paginator.paginate_queryset(products, request)

        response_data = {
            "count": paginator.page.paginator.count,
            "next": paginator.get_next_link(),
            "previous": paginator.get_previous_link(),
            "results": result_page,
        }

        cache.set(cache_key, response_data, timeout=60 * 15)
        return Response(response_data)

class ProductDetailView(APIView):
    def get(self, request, product_id):
        query = f"""
            SELECT 
                p.product_id,
                p.product_code,
                p.product_name_ar,
                p.product_name_en,
                p.sell_price,
                p.product_image_url,

                -- Get company details
                JSON_QUERY((
                    SELECT 
                        c.company_id,
                        c.co_name_en,
                        c.co_name_ar
                    FROM Companys c
                    WHERE c.company_id = p.company_id
                    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER
                )) AS company,

                -- Get product group details
                JSON_QUERY((
                    SELECT 
                        pg.group_id,
                        pg.group_name_en,
                        pg.group_name_ar
                    FROM Product_groups pg
                    WHERE pg.group_id = p.group_id
                    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER
                )) AS product_group,

                -- Calculate amount, replace NULL with 0
                ISNULL((
                    SELECT CAST(SUM(pa.amount) AS INT) 
                    FROM Product_Amount pa 
                    WHERE pa.product_id = p.product_id
                ), 0) AS amount

            FROM Products p
            WHERE p.product_id = {product_id}
        """

        with connection.cursor() as cursor:
            cursor.execute(query)
            columns = [col[0] for col in cursor.description]
            row = cursor.fetchone()

        if row is None:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)

        product = dict(zip(columns, row))
        product['company'] = json.loads(product['company']) if product['company'] else None
        product['product_group'] = json.loads(product['product_group']) if product['product_group'] else None

        return Response(product)













