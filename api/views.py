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
from .models import Product, DeviceToken, App_Order, App_OrderItem, AppUser, OrderStatus
from .serializers import ProductSearchSerializer, UserProfileSerializer, OrderListSerializer, OrderStatusSerializer, ProductSerializer, BestSellerProductSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import connection
from django.db.models import Q, Sum
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

        # Check if the paginated data is cached
        cached_data = cache.get(cache_key)
        if cached_data:
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
                (
                select pd.pd_name_ar
                )as product_description,
                (
                    SELECT STRING_AGG(pi.image_url, ', ')
                    FROM Product_Images pi
                    WHERE pi.product_id = p.product_id
                ) AS product_images
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
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()

        # Convert the rows into a list of dictionaries
        products = []
        for row in rows:
            product = dict(zip(columns, row))
            # Split the product_images string into a list of URLs
            if product['product_images']:
                product['product_images'] = product['product_images'].split(', ')
            else:
                product['product_images'] = []
            
            products.append(product)

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
                (
                select pd.pd_name_ar
                )as product_description,
                (
                    SELECT STRING_AGG(pi.image_url, ', ')
                    FROM Product_Images pi
                    WHERE pi.product_id = p.product_id
                ) AS product_images
            FROM Products p
            LEFT JOIN Product_groups pg ON p.group_id = pg.group_id
            LEFT JOIN Companys c ON p.company_id = c.company_id
            LEFT JOIN Product_description pd on pd.pd_id=p.pd_id
            WHERE p.company_id = {company_id}
        """

        with connection.cursor() as cursor:
            cursor.execute(query)
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()

        products = []
        for row in rows:
            product = dict(zip(columns, row))
            if product['product_images']:
                product['product_images'] = product['product_images'].split(', ')
            else:
                product['product_images'] = []
            
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
                (
                select pd.pd_name_ar
                )as product_description,
                (
                    SELECT STRING_AGG(pi.image_url, ', ')
                    FROM Product_Images pi
                    WHERE pi.product_id = p.product_id
                ) AS product_images
            FROM Products p
            LEFT JOIN Product_groups pg ON p.group_id = pg.group_id
            LEFT JOIN Companys c ON p.company_id = c.company_id
            LEFT JOIN Product_description pd on pd.pd_id=p.pd_id
            WHERE pg.category_id = {group_id}
        """

        with connection.cursor() as cursor:
            cursor.execute(query)
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()

        products = []
        for row in rows:
            product = dict(zip(columns, row))
            if product['product_images']:
                product['product_images'] = product['product_images'].split(', ')
            else:
                product['product_images'] = []
            
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

class BestSellersView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        # Get the page number from the request
        page_number = request.query_params.get('page', 1)
        cache_key = f'best_sellers_page_{page_number}'
        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data)

        # First, get the best selling product IDs
        best_sellers = (
            App_OrderItem.objects.values('product_id')
            .annotate(total_sold=Sum('quantity'))
            .order_by('-total_sold')[:50]  # Get top 50 for pagination
        )
        product_ids = [item['product_id'] for item in best_sellers]
        
        if not product_ids:
            return Response({
                "count": 0,
                "next": None,
                "previous": None,
                "results": [],
            })

        # Create a list of product IDs for the SQL IN clause
        product_ids_str = ','.join(map(str, product_ids))
        
        # Define the raw SQL query with the same structure as other product views
        query = f"""
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
                (
                select pd.pd_name_ar
                )as product_description,
                (
                    SELECT STRING_AGG(pi.image_url, ', ')
                    FROM Product_Images pi
                    WHERE pi.product_id = p.product_id
                ) AS product_images,
                -- Add total_sold information
                (
                    SELECT CAST(SUM(oi.quantity) AS INT)
                    FROM App_OrderItem oi
                    WHERE oi.product_id = p.product_id
                ) AS total_sold
            FROM 
                Products p
            LEFT JOIN 
                Product_groups pg ON p.group_id = pg.group_id
            LEFT JOIN 
                Companys c ON p.company_id = c.company_id
            LEFT JOIN 
                Product_description pd on pd.pd_id=p.pd_id
            WHERE p.product_id IN ({product_ids_str})
            ORDER BY total_sold DESC
        """

        # Execute the raw SQL query
        with connection.cursor() as cursor:
            cursor.execute(query)
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()

        # Convert the rows into a list of dictionaries
        products = []
        for row in rows:
            product = dict(zip(columns, row))
            # Split the product_images string into a list of URLs
            if product['product_images']:
                product['product_images'] = product['product_images'].split(', ')
            else:
                product['product_images'] = []
            
            products.append(product)

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

        # Cache the entire response
        cache.set(cache_key, response_data, timeout=60 * 15)  # Cache for 15 minutes

        # Return the response
        return Response(response_data)

class SeeOurProductsView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        page_number = request.query_params.get('page', 1)
        cache_key = f'see_our_products_page_{page_number}'
        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data)

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
                (
                select pd.pd_name_ar
                )as product_description,
                (
                    SELECT STRING_AGG(pi.image_url, ', ')
                    FROM Product_Images pi
                    WHERE pi.product_id = p.product_id
                ) AS product_images
            FROM 
                Products p
            LEFT JOIN 
                Product_groups pg ON p.group_id = pg.group_id
            LEFT JOIN 
                Companys c ON p.company_id = c.company_id
            LEFT JOIN 
                Product_description pd on pd.pd_id=p.pd_id
        """

        with connection.cursor() as cursor:
            cursor.execute(query)
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()

        products = []
        for row in rows:
            product = dict(zip(columns, row))
            if product['product_images']:
                product['product_images'] = product['product_images'].split(', ')
            else:
                product['product_images'] = []
            # Only include products with amount > 0
            if product.get('amount', 0) and int(product['amount']) > 0:
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

class AllUsersView(APIView):
    permission_classes = [IsAdminUser]  # Only admin users can see all users
    
    def get(self, request):
        page_number = request.query_params.get('page', 1)
        cache_key = f'all_users_page_{page_number}'
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return Response(cached_data)

        # Get all users with their complete information
        users = AppUser.objects.all().order_by('-created_at')
        
        # Convert to list of dictionaries with all user information
        users_data = []
        for user in users:
            # Get user's orders for statistics
            user_orders = App_Order.objects.filter(user=user)
            total_orders = user_orders.count()
            total_spent = float(user_orders.aggregate(total=Sum('total_price'))['total'] or 0)
            avg_order_value = total_spent / total_orders if total_orders > 0 else 0
            
            # Get order status distribution
            status_counts = {}
            for status_choice in OrderStatus.choices:
                status_counts[status_choice[0]] = user_orders.filter(status=status_choice[0]).count()
            
            user_data = {
                'id': user.id,
                'email': user.email,
                'phone': user.phone,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'birthdate': user.birthdate,
                'gender': user.gender,
                'auth_type': user.auth_type,
                'social_id': user.social_id,
                'profile_picture': user.profile_picture,
                'is_active': user.is_active,
                'is_staff': user.is_staff,
                'created_at': user.created_at,
                'updated_at': user.updated_at,
                'last_login': user.last_login,
                # Additional computed fields
                'full_name': f"{user.first_name or ''} {user.last_name or ''}".strip() or None,
                'total_orders': total_orders,
                'total_spent': total_spent,
                'avg_order_value': round(avg_order_value, 2),
                'last_order_date': user_orders.order_by('-created_at').values_list('created_at', flat=True).first(),
                'first_order_date': user_orders.order_by('created_at').values_list('created_at', flat=True).first(),
                'order_status_distribution': status_counts,
            }
            users_data.append(user_data)

        # Set up pagination
        paginator = PageNumberPagination()
        paginator.page_size = 20
        result_page = paginator.paginate_queryset(users_data, request)

        # Build the response data
        response_data = {
            "count": paginator.page.paginator.count,
            "next": paginator.get_next_link(),
            "previous": paginator.get_previous_link(),
            "results": result_page,
        }

        # Cache the response
        cache.set(cache_key, response_data, timeout=60 * 5)  # Cache for 5 minutes

        return Response(response_data)

class UserDetailView(APIView):
    permission_classes = [IsAdminUser]  # Only admin users can see user details
    
    def get(self, request, user_id):
        try:
            user = AppUser.objects.get(id=user_id)
        except AppUser.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Get user's orders with items
        orders = App_Order.objects.filter(user=user).prefetch_related('items').order_by('-created_at')
        
        # Prepare order history
        order_history = []
        for order in orders:
            order_data = {
                'order_id': order.id,
                'created_at': order.created_at,
                'status': order.status,
                'total_price': float(order.total_price),
                'payment_method': order.payment_method,
                'delivery_method': order.delivery_method,
                'address_name': order.address_name,
                'address_street': order.address_street,
                'latitude': order.latitude,
                'longitude': order.longitude,
                'is_home_delivery': order.is_home_delivery,
                'call_request_enabled': order.call_request_enabled,
                'promo_code': order.promo_code,
                'items': []
            }
            
            # Add order items
            for item in order.items.all():
                # Convert unit_type from ID to name
                unit_type_name = item.unit_type
                try:
                    with connection.cursor() as cursor:
                        cursor.execute("""
                            SELECT unit_name_ar 
                            FROM Product_units 
                            WHERE unit_id = %s
                        """, [item.unit_type])
                        result = cursor.fetchone()
                        unit_type_name = result[0] if result else item.unit_type
                except Exception:
                    unit_type_name = item.unit_type
                
                item_data = {
                    'product_id': int(item.product_id),
                    'product_name_en': item.product_name_en,
                    'product_name_ar': item.product_name_ar,
                    'unit_price': float(item.unit_price),
                    'quantity': item.quantity,
                    'item_total': float(item.item_total),
                    'unit_type': unit_type_name,
                }
                order_data['items'].append(item_data)
            
            order_history.append(order_data)
        
        # Calculate user statistics
        total_orders = orders.count()
        total_spent = float(orders.aggregate(total=Sum('total_price'))['total'] or 0)
        avg_order_value = total_spent / total_orders if total_orders > 0 else 0
        
        # Get order status distribution
        status_counts = {}
        for status_choice in OrderStatus.choices:
            status_counts[status_choice[0]] = orders.filter(status=status_choice[0]).count()
        
        # Prepare user data
        user_data = {
            'id': user.id,
            'email': user.email,
            'phone': user.phone,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'birthdate': user.birthdate,
            'gender': user.gender,
            'auth_type': user.auth_type,
            'social_id': user.social_id,
            'profile_picture': user.profile_picture,
            'is_active': user.is_active,
            'is_staff': user.is_staff,
            'created_at': user.created_at,
            'updated_at': user.updated_at,
            'last_login': user.last_login,
            'full_name': f"{user.first_name or ''} {user.last_name or ''}".strip() or None,
            
            # Order statistics
            'total_orders': total_orders,
            'total_spent': total_spent,
            'avg_order_value': round(avg_order_value, 2),
            'last_order_date': orders.first().created_at if orders.exists() else None,
            'first_order_date': orders.last().created_at if orders.exists() else None,
            'order_status_distribution': status_counts,
            
            # Order history
            'order_history': order_history
        }
        
        return Response(user_data)

class DashboardView(APIView):
    permission_classes = [IsAdminUser]  # Only admin users can access dashboard
    
    def get(self, request):
        cache_key = 'admin_dashboard_data'
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return Response(cached_data)

        # Get date range (last 30 days by default)
        from datetime import datetime, timedelta
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        # 1. Sales Analytics
        total_orders = App_Order.objects.count()
        total_revenue = float(App_Order.objects.aggregate(total=Sum('total_price'))['total'] or 0)
        
        # Recent orders (last 30 days)
        recent_orders = App_Order.objects.filter(created_at__gte=start_date)
        recent_orders_count = recent_orders.count()
        recent_revenue = float(recent_orders.aggregate(total=Sum('total_price'))['total'] or 0)
        
        # Average order value
        avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
        
        # 2. Order Status Distribution
        order_status_counts = {}
        for status_choice in OrderStatus.choices:
            order_status_counts[status_choice[0]] = App_Order.objects.filter(status=status_choice[0]).count()
        
        # 3. User Statistics
        total_users = AppUser.objects.count()
        active_users = AppUser.objects.filter(is_active=True).count()
        new_users_this_month = AppUser.objects.filter(created_at__gte=start_date).count()
        
        # 4. Product Performance
        # Top selling products
        top_products = (
            App_OrderItem.objects.values('product_id', 'product_name_en')
            .annotate(total_sold=Sum('quantity'))
            .order_by('-total_sold')[:10]
        )
        
        # Products with low stock (amount < 10)
        low_stock_products = []
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        p.product_id,
                        p.product_name_en,
                        p.product_name_ar,
                        ISNULL(SUM(pa.amount), 0) as total_stock
                    FROM Products p
                    LEFT JOIN Product_Amount pa ON p.product_id = pa.product_id
                    GROUP BY p.product_id, p.product_name_en, p.product_name_ar
                    HAVING ISNULL(SUM(pa.amount), 0) < 10
                    ORDER BY total_stock ASC
                """)
                columns = [col[0] for col in cursor.description]
                for row in cursor.fetchall():
                    low_stock_products.append(dict(zip(columns, row)))
        except Exception as e:
            print(f"Error getting low stock products: {e}")
        
        # 5. Recent Activity
        recent_orders_list = App_Order.objects.select_related('user').order_by('-created_at')[:10]
        recent_orders_data = []
        for order in recent_orders_list:
            recent_orders_data.append({
                'order_id': order.id,
                'customer_name': f"{order.user.first_name or ''} {order.user.last_name or ''}".strip() or order.user.email or order.user.phone,
                'customer_email': order.user.email,
                'customer_phone': order.user.phone,
                'total_amount': float(order.total_price),
                'status': order.status,
                'created_at': order.created_at,
                'payment_method': order.payment_method,
                'delivery_method': order.delivery_method,
            })
        
        # 6. Revenue Trends (last 7 days)
        daily_revenue = []
        for i in range(7):
            date = end_date - timedelta(days=i)
            day_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = date.replace(hour=23, minute=59, second=59, microsecond=999999)
            
            daily_total = App_Order.objects.filter(
                created_at__gte=day_start,
                created_at__lte=day_end
            ).aggregate(total=Sum('total_price'))['total'] or 0
            
            daily_revenue.append({
                'date': date.strftime('%Y-%m-%d'),
                'revenue': float(daily_total),
                'orders': App_Order.objects.filter(
                    created_at__gte=day_start,
                    created_at__lte=day_end
                ).count()
            })
        
        # 7. Payment Method Distribution
        payment_method_counts = {}
        payment_methods = App_Order.objects.values_list('payment_method', flat=True).distinct()
        for method in payment_methods:
            if method:
                payment_method_counts[method] = App_Order.objects.filter(payment_method=method).count()
        
        # 8. Delivery Method Distribution
        delivery_method_counts = {}
        delivery_methods = App_Order.objects.values_list('delivery_method', flat=True).distinct()
        for method in delivery_methods:
            if method:
                delivery_method_counts[method] = App_Order.objects.filter(delivery_method=method).count()
        
        # Build dashboard data
        dashboard_data = {
            # Sales Overview
            'sales_overview': {
                'total_orders': total_orders,
                'total_revenue': round(total_revenue, 2),
                'recent_orders_count': recent_orders_count,
                'recent_revenue': round(recent_revenue, 2),
                'avg_order_value': round(avg_order_value, 2),
            },
            
            # Order Status
            'order_status_distribution': order_status_counts,
            
            # User Statistics
            'user_statistics': {
                'total_users': total_users,
                'active_users': active_users,
                'new_users_this_month': new_users_this_month,
                'user_growth_rate': round((new_users_this_month / total_users * 100), 2) if total_users > 0 else 0,
            },
            
            # Product Performance
            'product_performance': {
                'top_selling_products': list(top_products),
                'low_stock_products': low_stock_products,
                'low_stock_count': len(low_stock_products),
            },
            
            # Recent Activity
            'recent_activity': {
                'recent_orders': recent_orders_data,
            },
            
            # Trends
            'revenue_trends': {
                'daily_revenue': list(reversed(daily_revenue)),  # Reverse to show oldest first
            },
            
            # Payment & Delivery
            'payment_method_distribution': payment_method_counts,
            'delivery_method_distribution': delivery_method_counts,
            
            # Quick Stats
            'quick_stats': {
                'pending_orders': order_status_counts.get('pending', 0),
                'delivered_orders': order_status_counts.get('delivered', 0),
                'cancelled_orders': order_status_counts.get('cancelled', 0),
                'total_products': Product.objects.count(),
                'products_in_stock': len([p for p in low_stock_products if p.get('total_stock', 0) > 0]),
            }
        }
        
        # Cache for 5 minutes
        cache.set(cache_key, dashboard_data, timeout=60 * 5)
        
        return Response(dashboard_data)
