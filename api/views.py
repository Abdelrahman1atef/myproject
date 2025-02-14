# # api/views.py

from rest_framework.pagination import PageNumberPagination
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Product, ProductGroup,Companys
from django.db.models import Prefetch
from .serializers import ProductSerializer
from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader
from django.db import connection
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.core.cache import cache

def home(request):
    return render(request, 'api/api_list.html')

class ProductListView(APIView):
    def get(self, request):
        # Check if the data is cached
        cached_data = cache.get('product_list')
        if cached_data:
            return Response(cached_data)
        # Define the raw SQL query
        query = """
            SELECT 
                p.product_id,
                p.product_code,
                p.product_name_ar,
                p.product_name_en,
                p.sell_price,
                p.company_id,
                p.group_id,
                p.product_image_url,
                pg.group_name_en AS group_name_en,
                pg.group_name_ar AS group_name_ar,
                c.co_name_en AS co_name_en,
                c.co_name_ar AS co_name_ar
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
            products.append(product)

        # Set up pagination
        paginator = PageNumberPagination()
        paginator.page_size = 20
        result_page = paginator.paginate_queryset(products, request)

        # # Cache the results
        # cache.set('product_list', result_page, timeout=60 * 15)  # Cache for 15 minutes
        # Return paginated data as a JSON response
        return paginator.get_paginated_response(result_page)
#     def get(self, request):
#         # Query all products from the database
#         products = Product.objects.all()
#  # Prefetch related ProductGroup and Companys data
#         group_ids = products.values_list('group_id', flat=True).distinct()
#         company_ids = products.values_list('company_id', flat=True).distinct()

#         product_groups = {pg.group_id: pg for pg in ProductGroup.objects.filter(group_id__in=group_ids)}
#         companies = {c.company_id: c for c in Companys.objects.filter(company_id__in=company_ids)}

#         # Attach related data to products
#         for product in products:
#             product.product_group = product_groups.get(product.group_id)
#             product.company = companies.get(product.company_id)

#         # # Render the data into an HTML template
#         # template = loader.get_template('api/products.html')
#         # context = {'products': products}
#         # return HttpResponse(template.render(context, request))

#         # Set up pagination
#         paginator = PageNumberPagination()
#         paginator.page_size = 100  # Set the page size to 10 items per page
#         result_page = paginator.paginate_queryset(products, request)

#         # Serialize the data
#         serializer = ProductSerializer(result_page, many=True)

#         # Return paginated data as a JSON response
#         return paginator.get_paginated_response(serializer.data)

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
