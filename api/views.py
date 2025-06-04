# # api/views.py

from rest_framework.pagination import PageNumberPagination
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import render
from django.db import connection
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.core.cache import cache
import json
from rest_framework import status
from .models import Product, DeviceToken, App_Order
from .serializers import ProductSearchSerializer, UserProfileSerializer, OrderListSerializer, OrderStatusSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import connection
from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from .serializers import AppUserSerializer, LoginSerializer,OrderCreateSerializer, DeviceTokenSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Product
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from rest_framework.permissions import IsAdminUser
from rest_framework.generics import ListAPIView
from rest_framework import generics, permissions

def home(request):
    return render(request, 'api/api_list.html')

class CategoryView(APIView):   
    permission_classes = [AllowAny]
    def get(self, request):
        query = """
            select *
            from Product_Categories
        """

        with connection.cursor() as cursor:
            cursor.execute(query)
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()

        groups = []
        for row in rows:
            group = dict(zip(columns, row))
            groups.append(group)

        return Response(groups)
    
class ProductSearchView(APIView):
    permission_classes = [AllowAny]
    def get(self, request, *args, **kwargs):
        # Get the search query from the URL parameter
        query = request.query_params.get('q', None)

        if query:
            cache_key = f"search_{query}"
            cached_results = cache.get(cache_key)
            if cached_results:
                return Response(cached_results, status=status.HTTP_200_OK)
            
            products = Product.objects.filter(
                Q(product_name_en__icontains=query) |
                Q(product_name_ar__icontains=query)
            )[:20]
            product = Product.objects.filter(product_name_en__icontains="test").first()
            serializer = ProductSearchSerializer(product)
            print(serializer.data)
            
            serializer = ProductSearchSerializer(products, many=True)
            cache.set(cache_key, serializer.data, timeout=60)  # Cache for 60 seconds
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response([], status=status.HTTP_200_OK)    
    
class ProductListView(APIView):
    permission_classes = [AllowAny]
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
                (
				select unit_name_ar
				from Product_units pu
				where pu.unit_id=p.product_unit1
				)as product_unit1,
                p.sell_price,

				(
				select unit_name_ar
				from Product_units pu
				where pu.unit_id=p.product_unit2
				)as product_unit2,
				p.product_unit1_2,
				p.unit2_sell_price,
				(
				select unit_name_ar
				from Product_units pu
				where pu.unit_id=p.product_unit3
				)as product_unit3,
				p.product_unit1_3,
				p.unit3_sell_price,
				ISNULL(
                    (SELECT CAST(SUM(pa.amount) AS INT) 
                     FROM Product_Amount pa
                     WHERE pa.product_id = p.product_id), 
                    0
                ) AS amount,
                p.product_image_url,
                (
                select pd.pd_name_ar
                )as product_description,
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
                (
                    SELECT STRING_AGG(pi.image_url, ', ') -- Concatenate image URLs into a single string
                    FROM Product_Images pi
                    WHERE pi.product_id = p.product_id
                ) AS product_images -- Returns all image URLs as a comma-separated string
                
            FROM 
                Products p
            LEFT JOIN 
                Product_groups pg ON p.group_id = pg.group_id
            LEFT JOIN 
                Companys c ON p.company_id = c.company_id
            LEFT JOIN 
                Product_description pd on pd.pd_id=p.pd_id
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
            # Split the product_images string into a list of URLs
            if product['product_images']:
                product['product_images'] = product['product_images'].split(', ')
            else:
                product['product_images'] = []  # Empty list if no images exist
            
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
    permission_classes = [AllowAny]
    def get(self, request, company_id):
        page_number = request.query_params.get('page', 1)
        cache_key = f'product_list_company_{company_id}_page_{page_number}'
        cached_data = cache.get(cache_key)

        if cached_data:
            return Response(cached_data)
        query = f"""
            {query_head}
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
            # Split the product_images string into a list of URLs
            if product['product_images']:
                product['product_images'] = product['product_images'].split(', ')
            else:
                product['product_images'] = []  # Empty list if no images exist
            
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
    permission_classes = [AllowAny]
    def get(self, request, group_id):
        page_number = request.query_params.get('page', 1)
        cache_key = f'product_list_group_{group_id}_page_{page_number}'
        cached_data = cache.get(cache_key)

        if cached_data:
            return Response(cached_data)

        query = f"""
            {query_head}
            WHERE pg.category_id = {group_id}
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
            # Split the product_images string into a list of URLs
            if product['product_images']:
                product['product_images'] = product['product_images'].split(', ')
            else:
                product['product_images'] = []  # Empty list if no images exist
            
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
    permission_classes = [AllowAny]
    def get(self, request, product_id):
        query = f"""
            {query_head}
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
        # Split the product_images string into a list of URLs
        if product['product_images']:
            product['product_images'] = product['product_images'].split(', ')
        else:
            product['product_images'] = []  # Empty list if no images exist
            
        return Response(product)

class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        serializer = UserProfileSerializer(user)
        return Response(serializer.data)

class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = AppUserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        # Handle errors
        errors = serializer.errors

        # Build custom message
        email_error = 'email' in errors
        phone_error = 'phone' in errors

        if email_error and phone_error:
            custom_error = "The email or phone number you've entered is already registered. Please try logging in or use different details to sign up."
        elif email_error:
            custom_error = "This email is already taken. Please try a different one or log in."
        elif phone_error:
            custom_error = "This phone number is already registered. Please use another or log in."
        else:
            custom_error = "Please fix the errors below."

        # Return consistent format
        return Response({
            "message": custom_error,
            "status_code": status.HTTP_400_BAD_REQUEST,
            "errors": {
                "non_field_errors": [custom_error]
            }
        }, status=status.HTTP_400_BAD_REQUEST)
    
class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data  # This already has the correct full response.

        if user:
            return Response(user, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Token not found.'}, status=status.HTTP_400_BAD_REQUEST)

class CreateOrderView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        # Pass the request context to the serializer
        serializer = OrderCreateSerializer(data=request.data, context={'request': request})

        if serializer.is_valid():
            order = serializer.save()

            # Notify admin via WebSocket
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                "orders",  # Must match consumer group name
                {
                    "type": "order.notification",  # Must match consumer method
                    "message": f"New order #{order.id}",
                    "order_id": order.id,
                    "customer": order.user.email
                }
            )

            return Response({
                "status": "success",
                "message": "Order created successfully",
                "order_id": order.id,
                "total_amount": order.total_price,
                }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AdminOrderListView(ListAPIView):
    queryset = App_Order.objects.prefetch_related('items').select_related('user').all()
    serializer_class = OrderListSerializer
    permission_classes = [IsAdminUser]  # Only allow admin users

class CustomerOrderListView(ListAPIView):
    serializer_class = OrderListSerializer
    permission_classes = [IsAuthenticated]  # User must be logged in

    def get_queryset(self):
        # Get orders for the currently logged-in user
        return App_Order.objects.filter(user=self.request.user)\
                               .prefetch_related('items')\
                               .select_related('user')\
                               .order_by('-created_at')
    
class OrderStatusUpdateAPIView(generics.UpdateAPIView):
    queryset = App_Order.objects.all()
    serializer_class = OrderStatusSerializer
    permission_classes = [permissions.IsAdminUser]  # Only admins can change status

class DeviceTokenView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = DeviceTokenSerializer(data=request.data)
        if serializer.is_valid():
            token = serializer.validated_data['token']

            # Ensure one token per user (update if exists)
            DeviceToken.objects.update_or_create(
                user=request.user,
                defaults={'token': token}
            )

            return Response({'detail': 'Token saved successfully'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
      

query_head = """
           SELECT 
                p.product_id,
                p.product_code,
                p.product_name_ar,
                p.product_name_en,
                (
				select unit_name_ar
				from Product_units pu
				where pu.unit_id=p.product_unit1
				)as product_unit1,
                p.sell_price,

				(
				select unit_name_ar
				from Product_units pu
				where pu.unit_id=p.product_unit2
				)as product_unit2,
				p.product_unit1_2,
				p.unit2_sell_price,
				(
				select unit_name_ar
				from Product_units pu
				where pu.unit_id=p.product_unit3
				)as product_unit3,
				p.product_unit1_3,
				p.unit3_sell_price,
                ISNULL((
                    SELECT CAST(SUM(pa.amount) AS INT) 
                    FROM Product_Amount pa 
                    WHERE pa.product_id = p.product_id
                ), 0) AS amount,
                p.product_image_url,
                (
                select pd.pd_name_ar
                from Product_description pd
                where pd.pd_id=p.pd_id
                )as product_description,
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
                (
                    SELECT STRING_AGG(pi.image_url, ', ') -- Concatenate image URLs into a single string
                    FROM Product_Images pi
                    WHERE pi.product_id = p.product_id
                ) AS product_images -- Returns all image URLs as a comma-separated string
                

            FROM Products p
            -- Join with product_group to access category_id
			JOIN product_groups pg ON p.group_id = pg.group_id
                """
