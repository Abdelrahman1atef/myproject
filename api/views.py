# api/views.py

from datetime import timedelta
from rest_framework.pagination import PageNumberPagination
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import render
from django.db import connection
from django.core.cache import cache
import json
from rest_framework import status
from .models import (
    DeviceToken, Product, ProductUnit, ProductAmount, ProductImages, ProductDescription,
    ProductGroup, Companys, AppUser, App_Order, App_OrderItem, OrderStatus, ProductCategories
)
from django.db import models
from .serializers import ProductSearchSerializer, UserProfileSerializer, OrderListSerializer, OrderStatusSerializer, ProductSerializer, BestSellerProductSerializer
from django.db.models import Q, Sum
from rest_framework.permissions import AllowAny
from .serializers import AppUserSerializer, LoginSerializer,OrderCreateSerializer, DeviceTokenSerializer, RegisterWithOTPSerializer, VerifyOTPSerializer
from rest_framework.permissions import IsAuthenticated
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from rest_framework.permissions import IsAdminUser
from rest_framework.generics import ListAPIView
from rest_framework import generics, permissions
from .utils import send_fcm_notification_v1, send_otp_email, create_otp_record, verify_otp, validate_phone_number, is_otp_rate_limited, store_user_registration_data, get_user_registration_data, clear_user_registration_data
from django.utils import timezone
from django.contrib.auth.hashers import make_password
from django.conf import settings

def home(request):
    return render(request, 'api/api_list.html')

class CategoryView(APIView):   
    permission_classes = [AllowAny]
    def get(self, request):
        # Get all categories using ORM
        categories = ProductCategories.objects.all()
        
        # Convert to list of dictionaries
        categories_data = []
        for category in categories:
            category_data = {
                'category_id': category.category_id,
                'category_name_ar': category.category_name_ar
            }
            categories_data.append(category_data)

        return Response(categories_data)
    
class ProductSearchView(APIView):
    permission_classes = [AllowAny]
    def get(self, request, *args, **kwargs):
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
            product_ids = [product.product_id for product in products]
            stock_totals = ProductAmount.objects.filter(product_id__in=product_ids).values('product_id').annotate(total=models.Sum('amount'))
            stock_dict = {item['product_id']: item['total'] for item in stock_totals}
            unit_ids = set()
            for product in products:
                if product.product_unit1:
                    unit_ids.add(product.product_unit1)
                if product.product_unit2:
                    unit_ids.add(product.product_unit2)
                if product.product_unit3:
                    unit_ids.add(product.product_unit3)
            units = ProductUnit.objects.filter(unit_id__in=unit_ids)
            unit_dict = {unit.unit_id: unit.unit_name_ar for unit in units}
            images = ProductImages.objects.filter(product_id__in=product_ids)
            images_dict = {}
            for img in images:
                images_dict.setdefault(img.product_id, []).append(img.image_url)
            pd_ids = [product.pd_id for product in products if hasattr(product, 'pd_id') and product.pd_id]
            descriptions = ProductDescription.objects.filter(pd_id__in=pd_ids)
            desc_dict = {desc.pd_id: desc.pd_name_ar for desc in descriptions}
            results = []
            for product in products:
                total_amount = stock_dict.get(product.product_id, 0)
                product_unit1_name = unit_dict.get(product.product_unit1)
                product_unit2_name = unit_dict.get(product.product_unit2)
                product_unit3_name = unit_dict.get(product.product_unit3)
                product_description = None
                if hasattr(product, 'pd_id') and product.pd_id:
                    product_description = desc_dict.get(product.pd_id)
                product_images = images_dict.get(product.product_id, [])
                product_data = {
                    'product_id': product.product_id,
                    'product_code': product.product_code,
                    'product_name_ar': product.product_name_ar,
                    'product_name_en': product.product_name_en,
                    'product_unit1': product_unit1_name,
                    'sell_price': product.sell_price,
                    'product_unit2': product_unit2_name,
                    'product_unit1_2': product.product_unit1_2,
                    'unit2_sell_price': product.unit2_sell_price,
                    'product_unit3': product_unit3_name,
                    'product_unit1_3': product.product_unit1_3,
                    'unit3_sell_price': product.unit3_sell_price,
                    'amount': total_amount,
                    'product_description': product_description,
                    'product_images': list(product_images)
                }
                results.append(product_data)
            cache.set(cache_key, results, timeout=60)
            return Response(results, status=status.HTTP_200_OK)
        return Response([], status=status.HTTP_200_OK)    
    
class ProductListView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        page_number = request.query_params.get('page', 1)
        cache_key = f'product_list_page_{page_number}'
        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data)
        products_queryset = Product.objects.all()
        product_ids = [product.product_id for product in products_queryset]
        # Batch fetch all stock totals
        stock_totals = ProductAmount.objects.filter(product_id__in=product_ids).values('product_id').annotate(total=models.Sum('amount'))
        stock_dict = {item['product_id']: item['total'] for item in stock_totals}
        # Batch fetch all units
        unit_ids = set()
        for product in products_queryset:
            if product.product_unit1:
                unit_ids.add(product.product_unit1)
            if product.product_unit2:
                unit_ids.add(product.product_unit2)
            if product.product_unit3:
                unit_ids.add(product.product_unit3)
        units = ProductUnit.objects.filter(unit_id__in=unit_ids)
        unit_dict = {unit.unit_id: unit.unit_name_ar for unit in units}
        # Batch fetch all images
        images = ProductImages.objects.filter(product_id__in=product_ids)
        images_dict = {}
        for img in images:
            images_dict.setdefault(img.product_id, []).append(img.image_url)
        # Batch fetch all descriptions
        pd_ids = [product.pd_id for product in products_queryset if hasattr(product, 'pd_id') and product.pd_id]
        descriptions = ProductDescription.objects.filter(pd_id__in=pd_ids)
        desc_dict = {desc.pd_id: desc.pd_name_ar for desc in descriptions}
        products = []
        for product in products_queryset:
            total_amount = stock_dict.get(product.product_id, 0)
            product_unit1_name = unit_dict.get(product.product_unit1)
            product_unit2_name = unit_dict.get(product.product_unit2)
            product_unit3_name = unit_dict.get(product.product_unit3)
            product_description = None
            if hasattr(product, 'pd_id') and product.pd_id:
                product_description = desc_dict.get(product.pd_id)
            product_images = images_dict.get(product.product_id, [])
            product_data = {
                'product_id': product.product_id,
                'product_code': product.product_code,
                'product_name_ar': product.product_name_ar,
                'product_name_en': product.product_name_en,
                'product_unit1': product_unit1_name,
                'sell_price': product.sell_price,
                'product_unit2': product_unit2_name,
                'product_unit1_2': product.product_unit1_2,
                'unit2_sell_price': product.unit2_sell_price,
                'product_unit3': product_unit3_name,
                'product_unit1_3': product.product_unit1_3,
                'unit3_sell_price': product.unit3_sell_price,
                'amount': total_amount,
                'product_description': product_description,
                'product_images': list(product_images)
            }
            products.append(product_data)
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

class ProductListByCompanyView(APIView):
    permission_classes = [AllowAny]
    def get(self, request, company_id):
        page_number = request.query_params.get('page', 1)
        cache_key = f'product_list_company_{company_id}_page_{page_number}'
        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data)
        products_queryset = Product.objects.filter(company_id=company_id)
        product_ids = [product.product_id for product in products_queryset]
        stock_totals = ProductAmount.objects.filter(product_id__in=product_ids).values('product_id').annotate(total=models.Sum('amount'))
        stock_dict = {item['product_id']: item['total'] for item in stock_totals}
        unit_ids = set()
        for product in products_queryset:
            if product.product_unit1:
                unit_ids.add(product.product_unit1)
            if product.product_unit2:
                unit_ids.add(product.product_unit2)
            if product.product_unit3:
                unit_ids.add(product.product_unit3)
        units = ProductUnit.objects.filter(unit_id__in=unit_ids)
        unit_dict = {unit.unit_id: unit.unit_name_ar for unit in units}
        images = ProductImages.objects.filter(product_id__in=product_ids)
        images_dict = {}
        for img in images:
            images_dict.setdefault(img.product_id, []).append(img.image_url)
        pd_ids = [product.pd_id for product in products_queryset if hasattr(product, 'pd_id') and product.pd_id]
        descriptions = ProductDescription.objects.filter(pd_id__in=pd_ids)
        desc_dict = {desc.pd_id: desc.pd_name_ar for desc in descriptions}
        products = []
        for product in products_queryset:
            total_amount = stock_dict.get(product.product_id, 0)
            product_unit1_name = unit_dict.get(product.product_unit1)
            product_unit2_name = unit_dict.get(product.product_unit2)
            product_unit3_name = unit_dict.get(product.product_unit3)
            product_description = None
            if hasattr(product, 'pd_id') and product.pd_id:
                product_description = desc_dict.get(product.pd_id)
            product_images = images_dict.get(product.product_id, [])
            product_data = {
                'product_id': product.product_id,
                'product_code': product.product_code,
                'product_name_ar': product.product_name_ar,
                'product_name_en': product.product_name_en,
                'product_unit1': product_unit1_name,
                'sell_price': product.sell_price,
                'product_unit2': product_unit2_name,
                'product_unit1_2': product.product_unit1_2,
                'unit2_sell_price': product.unit2_sell_price,
                'product_unit3': product_unit3_name,
                'product_unit1_3': product.product_unit1_3,
                'unit3_sell_price': product.unit3_sell_price,
                'amount': total_amount,
                'product_description': product_description,
                'product_images': list(product_images)
            }
            products.append(product_data)
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
        products_queryset = Product.objects.filter(group_id=group_id)
        product_ids = [product.product_id for product in products_queryset]
        stock_totals = ProductAmount.objects.filter(product_id__in=product_ids).values('product_id').annotate(total=models.Sum('amount'))
        stock_dict = {item['product_id']: item['total'] for item in stock_totals}
        unit_ids = set()
        for product in products_queryset:
            if product.product_unit1:
                unit_ids.add(product.product_unit1)
            if product.product_unit2:
                unit_ids.add(product.product_unit2)
            if product.product_unit3:
                unit_ids.add(product.product_unit3)
        units = ProductUnit.objects.filter(unit_id__in=unit_ids)
        unit_dict = {unit.unit_id: unit.unit_name_ar for unit in units}
        images = ProductImages.objects.filter(product_id__in=product_ids)
        images_dict = {}
        for img in images:
            images_dict.setdefault(img.product_id, []).append(img.image_url)
        pd_ids = [product.pd_id for product in products_queryset if hasattr(product, 'pd_id') and product.pd_id]
        descriptions = ProductDescription.objects.filter(pd_id__in=pd_ids)
        desc_dict = {desc.pd_id: desc.pd_name_ar for desc in descriptions}
        products = []
        for product in products_queryset:
            total_amount = stock_dict.get(product.product_id, 0)
            product_unit1_name = unit_dict.get(product.product_unit1)
            product_unit2_name = unit_dict.get(product.product_unit2)
            product_unit3_name = unit_dict.get(product.product_unit3)
            product_description = None
            if hasattr(product, 'pd_id') and product.pd_id:
                product_description = desc_dict.get(product.pd_id)
            product_images = images_dict.get(product.product_id, [])
            product_data = {
                'product_id': product.product_id,
                'product_code': product.product_code,
                'product_name_ar': product.product_name_ar,
                'product_name_en': product.product_name_en,
                'product_unit1': product_unit1_name,
                'sell_price': product.sell_price,
                'product_unit2': product_unit2_name,
                'product_unit1_2': product.product_unit1_2,
                'unit2_sell_price': product.unit2_sell_price,
                'product_unit3': product_unit3_name,
                'product_unit1_3': product.product_unit1_3,
                'unit3_sell_price': product.unit3_sell_price,
                'amount': total_amount,
                'product_description': product_description,
                'product_images': list(product_images)
            }
            products.append(product_data)
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
        try:
            # Get the product with related data
            product = Product.objects.select_related().get(product_id=product_id)
            
            # Get company data
            company_data = None
            if product.company_id:
                try:
                    company = Companys.objects.get(company_id=product.company_id)
                    company_data = {
                        'company_id': company.company_id,
                        'co_name_en': company.co_name_en,
                        'co_name_ar': company.co_name_ar
                    }
                except Companys.DoesNotExist:
                    pass
            
            # Get product group data
            product_group_data = None
            if product.group_id:
                try:
                    product_group = ProductGroup.objects.get(group_id=product.group_id)
                    product_group_data = {
                        'group_id': product_group.group_id,
                        'group_name_en': product_group.group_name_en,
                        'group_name_ar': product_group.group_name_ar
                    }
                except ProductGroup.DoesNotExist:
                    pass
            
            # Get product unit names
            product_unit1_name = None
            product_unit2_name = None
            product_unit3_name = None
            
            if product.product_unit1:
                try:
                    unit1 = ProductUnit.objects.get(unit_id=product.product_unit1)
                    product_unit1_name = unit1.unit_name_ar
                except ProductUnit.DoesNotExist:
                    pass
            
            if product.product_unit2:
                try:
                    unit2 = ProductUnit.objects.get(unit_id=product.product_unit2)
                    product_unit2_name = unit2.unit_name_ar
                except ProductUnit.DoesNotExist:
                    pass
            
            if product.product_unit3:
                try:
                    unit3 = ProductUnit.objects.get(unit_id=product.product_unit3)
                    product_unit3_name = unit3.unit_name_ar
                except ProductUnit.DoesNotExist:
                    pass
            
            # Get product description
            product_description = None
            if hasattr(product, 'pd_id') and product.pd_id:
                try:
                    description = ProductDescription.objects.get(pd_id=product.pd_id)
                    product_description = description.pd_name_ar
                except ProductDescription.DoesNotExist:
                    pass
            
            # Calculate total amount (stock)
            total_amount = ProductAmount.objects.filter(product_id=product.product_id).aggregate(
                total=models.Sum('amount')
            )['total'] or 0
            
            # Get product images
            product_images = ProductImages.objects.filter(product_id=product.product_id).values_list('image_url', flat=True)
            
            # Build response data
            product_data = {
                'product_id': product.product_id,
                'product_code': product.product_code,
                'product_name_ar': product.product_name_ar,
                'product_name_en': product.product_name_en,
                'product_unit1': product_unit1_name,
                'sell_price': product.sell_price,
                'product_unit2': product_unit2_name,
                'product_unit1_2': product.product_unit1_2,
                'unit2_sell_price': product.unit2_sell_price,
                'product_unit3': product_unit3_name,
                'product_unit1_3': product.product_unit1_3,
                'unit3_sell_price': product.unit3_sell_price,
                'amount': total_amount,
                'product_image_url': product.product_image_url,
                'product_description': product_description,
                'company': company_data,
                'product_group': product_group_data,
                'product_images': list(product_images)
            }
            
            return Response(product_data)
            
        except Product.DoesNotExist:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        serializer = UserProfileSerializer(user)
        return Response(serializer.data)

class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterWithOTPSerializer(data=request.data)
        if serializer.is_valid():
            # Get validated data
            validated_data = serializer.validated_data
            email = validated_data.get('email')
            
            # Check rate limiting for OTP
            if is_otp_rate_limited(email):
                return Response({
                    'message': 'Please wait 1 minute before requesting another OTP',
                    'status': 'error'
                }, status=status.HTTP_429_TOO_MANY_REQUESTS)
            
            # Store user registration data in cache
            user_data = validated_data.copy()
            user_data['password'] = make_password(user_data['password'])
            store_user_registration_data(email, user_data)
            
            # Create OTP and send email automatically
            try:
                otp_data = create_otp_record(email)
                
                # Send OTP email
                if send_otp_email(email, otp_data['otp_code']):
                    return Response({
                        'message': f'Registration information received. OTP sent to {email}',
                        'status': 'otp_sent',
                        'email': email,
                        'expires_in_minutes': settings.OTP_EXPIRY_MINUTES
                    }, status=status.HTTP_200_OK)
                else:
                    # Clear stored data if email sending failed
                    clear_user_registration_data(email)
                    return Response({
                        'message': 'Failed to send OTP email',
                        'status': 'error'
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                    
            except Exception as e:
                # Clear stored data if OTP creation failed
                clear_user_registration_data(email)
                return Response({
                    'message': f'Error creating OTP: {str(e)}',
                    'status': 'error'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
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

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        old_status = instance.status
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        new_status = serializer.instance.status
        # Only notify if status actually changed
        if old_status != new_status:
            # Notify the user if they have a device token
            user_tokens = DeviceToken.objects.filter(user=instance.user).values_list('token', flat=True)
            for token in user_tokens:
                send_fcm_notification_v1(
                    token,
                    title="Order Status Updated",
                    body=f"Your order (ID: {instance.id}) status changed to {new_status}.",
                    data={"order_id": instance.id, "new_status": new_status}
                )
        return Response(serializer.data)

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

class DeviceTokenRegisterView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = DeviceTokenSerializer(data=request.data)
        if serializer.is_valid():
            token = serializer.validated_data['token']
            # Remove this token from any other user
            DeviceToken.objects.filter(token=token).exclude(user=request.user).delete()
            # Update or create for this user
            device_token, created = DeviceToken.objects.update_or_create(
                user=request.user, token=token,
                defaults={}
            )
            return Response({'message': 'Token registered.'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
      



class BestSellersView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        page_number = request.query_params.get('page', 1)
        cache_key = f'best_sellers_page_{page_number}'
        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data)
        best_sellers = (
            App_OrderItem.objects.values('product_id')
            .annotate(total_sold=Sum('quantity'))
            .order_by('-total_sold')[:50]
        )
        product_ids = [item['product_id'] for item in best_sellers]
        if not product_ids:
            return Response({
                "count": 0,
                "next": None,
                "previous": None,
                "results": [],
            })
        products_queryset = Product.objects.filter(product_id__in=product_ids)
        stock_totals = ProductAmount.objects.filter(product_id__in=product_ids).values('product_id').annotate(total=models.Sum('amount'))
        stock_dict = {item['product_id']: item['total'] for item in stock_totals}
        unit_ids = set()
        for product in products_queryset:
            if product.product_unit1:
                unit_ids.add(product.product_unit1)
            if product.product_unit2:
                unit_ids.add(product.product_unit2)
            if product.product_unit3:
                unit_ids.add(product.product_unit3)
        units = ProductUnit.objects.filter(unit_id__in=unit_ids)
        unit_dict = {unit.unit_id: unit.unit_name_ar for unit in units}
        images = ProductImages.objects.filter(product_id__in=product_ids)
        images_dict = {}
        for img in images:
            images_dict.setdefault(img.product_id, []).append(img.image_url)
        pd_ids = [product.pd_id for product in products_queryset if hasattr(product, 'pd_id') and product.pd_id]
        descriptions = ProductDescription.objects.filter(pd_id__in=pd_ids)
        desc_dict = {desc.pd_id: desc.pd_name_ar for desc in descriptions}
        # Batch fetch total sold for all products
        sold_dict = {item['product_id']: item['total_sold'] for item in best_sellers}
        products = []
        for product in products_queryset:
            total_amount = stock_dict.get(product.product_id, 0)
            product_unit1_name = unit_dict.get(product.product_unit1)
            product_unit2_name = unit_dict.get(product.product_unit2)
            product_unit3_name = unit_dict.get(product.product_unit3)
            product_description = None
            if hasattr(product, 'pd_id') and product.pd_id:
                product_description = desc_dict.get(product.pd_id)
            product_images = images_dict.get(product.product_id, [])
            total_sold = sold_dict.get(product.product_id, 0)
            product_data = {
                'product_id': product.product_id,
                'product_code': product.product_code,
                'product_name_ar': product.product_name_ar,
                'product_name_en': product.product_name_en,
                'product_unit1': product_unit1_name,
                'sell_price': product.sell_price,
                'product_unit2': product_unit2_name,
                'product_unit1_2': product.product_unit1_2,
                'unit2_sell_price': product.unit2_sell_price,
                'product_unit3': product_unit3_name,
                'product_unit1_3': product.product_unit1_3,
                'unit3_sell_price': product.unit3_sell_price,
                'amount': total_amount,
                'product_description': product_description,
                'product_images': list(product_images),
                'total_sold': total_sold
            }
            products.append(product_data)
        products.sort(key=lambda x: x['total_sold'], reverse=True)
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

class SeeOurProductsView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        try:
            page_number = request.query_params.get('page', 1)
            cache_key = f'see_our_products_page_{page_number}'
            cached_data = cache.get(cache_key)
            if cached_data:
                return Response(cached_data)

            # Get all product_ids that are in stock (amount > 0)
            in_stock_ids = list(ProductAmount.objects.filter(amount__gt=0).values_list('product_id', flat=True).distinct())
            products_queryset = Product.objects.filter(product_id__in=in_stock_ids)

            # Batch fetch all stock totals for these products
            stock_totals = ProductAmount.objects.filter(product_id__in=in_stock_ids).values('product_id').annotate(total=models.Sum('amount'))
            stock_dict = {item['product_id']: item['total'] for item in stock_totals}

            # Batch fetch all units
            unit_ids = set()
            for product in products_queryset:
                if product.product_unit1:
                    unit_ids.add(product.product_unit1)
                if product.product_unit2:
                    unit_ids.add(product.product_unit2)
                if product.product_unit3:
                    unit_ids.add(product.product_unit3)
            units = ProductUnit.objects.filter(unit_id__in=unit_ids)
            unit_dict = {unit.unit_id: unit.unit_name_ar for unit in units}

            # Batch fetch all images
            images = ProductImages.objects.filter(product_id__in=in_stock_ids)
            images_dict = {}
            for img in images:
                images_dict.setdefault(img.product_id, []).append(img.image_url)

            # Batch fetch all descriptions
            pd_ids = [product.pd_id for product in products_queryset if hasattr(product, 'pd_id') and product.pd_id]
            descriptions = ProductDescription.objects.filter(pd_id__in=pd_ids)
            desc_dict = {desc.pd_id: desc.pd_name_ar for desc in descriptions}

            products = []
            for product in products_queryset:
                total_amount = stock_dict.get(product.product_id, 0)
                product_unit1_name = unit_dict.get(product.product_unit1)
                product_unit2_name = unit_dict.get(product.product_unit2)
                product_unit3_name = unit_dict.get(product.product_unit3)
                product_description = None
                if hasattr(product, 'pd_id') and product.pd_id:
                    product_description = desc_dict.get(product.pd_id)
                product_images = images_dict.get(product.product_id, [])
                product_data = {
                    'product_id': product.product_id,
                    'product_code': product.product_code,
                    'product_name_ar': product.product_name_ar,
                    'product_name_en': product.product_name_en,
                    'product_unit1': product_unit1_name,
                    'sell_price': product.sell_price,
                    'product_unit2': product_unit2_name,
                    'product_unit1_2': product.product_unit1_2,
                    'unit2_sell_price': product.unit2_sell_price,
                    'product_unit3': product_unit3_name,
                    'product_unit1_3': product.product_unit1_3,
                    'unit3_sell_price': product.unit3_sell_price,
                    'amount': total_amount,
                    'product_description': product_description,
                    'product_images': list(product_images)
                }
                products.append(product_data)
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
        except Exception as e:
            import traceback; traceback.print_exc()
            return Response({"error": str(e)}, status=500)

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
                    unit = ProductUnit.objects.get(unit_id=item.unit_type)
                    unit_type_name = unit.unit_name_ar
                except ProductUnit.DoesNotExist:
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
        from datetime import timedelta
        end_date = timezone.now()
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
        
        # Products with zero stock (out of stock) - Limited to top 20 most critical
        out_of_stock_products = []
        try:
            # Get all product_ids and their total stock
            stock_totals = ProductAmount.objects.values('product_id').annotate(total=models.Sum('amount'))
            zero_stock_ids = [item['product_id'] for item in stock_totals if not item['total'] or item['total'] == 0]
            # Also include products that have no ProductAmount rows at all
            all_product_ids = set(Product.objects.values_list('product_id', flat=True))
            stocked_product_ids = set(item['product_id'] for item in stock_totals)
            no_amount_ids = list(all_product_ids - stocked_product_ids)
            zero_stock_ids += no_amount_ids
            products_with_stock = Product.objects.filter(product_id__in=zero_stock_ids).order_by('product_name_en')[:20]
            for product in products_with_stock:
                out_of_stock_products.append({
                    'product_id': product.product_id,
                    'product_name_en': product.product_name_en,
                    'product_name_ar': product.product_name_ar,
                    'total_stock': 0
                })
        except Exception as e:
            print(f"Error getting out of stock products: {e}")
        
        # Get total count of out of stock products
        total_out_of_stock_count = 0
        try:
            total_out_of_stock_count = len(zero_stock_ids)
        except Exception as e:
            print(f"Error getting out of stock count: {e}")
        
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
            'dashboard_result': {
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
                'out_of_stock_products': out_of_stock_products,
                'out_of_stock_count': total_out_of_stock_count,
                'out_of_stock_products_shown': len(out_of_stock_products),
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
                'out_of_stock_products': total_out_of_stock_count,  # Products with zero stock
            }
            }
        }
        
        # Cache for 5 minutes
        cache.set(cache_key, dashboard_data, timeout=60 * 5)
        
        return Response(dashboard_data)

class VerifyOTPView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            otp_code = serializer.validated_data['otp_code']
            
            # Verify OTP
            is_valid, message = verify_otp(email, otp_code)
            
            if is_valid:
                # Get the stored user registration data
                user_data = get_user_registration_data(email)
                
                if not user_data:
                    return Response({
                        'message': 'Registration data not found. Please register again.',
                        'status': 'error'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                try:
                    # Mark email as verified and user as active
                    user_data['is_email_verified'] = True
                    user_data['is_active'] = True
                    
                    # Create user with all the stored data
                    user = AppUser.objects.create(**user_data)
                    
                    # Clear the stored registration data
                    clear_user_registration_data(email)
                    
                    # Generate token for the new user
                    from rest_framework.authtoken.models import Token
                    token, created = Token.objects.get_or_create(user=user)
                    
                    return Response({
                        'message': 'Email verified successfully! Account created.',
                        'status': 'success',
                        'user': {
                            'id': user.id,
                            'email': user.email,
                            'phone': user.phone,
                            'first_name': user.first_name,
                            'last_name': user.last_name,
                            'is_email_verified': user.is_email_verified,
                            'is_active': user.is_active,
                        },
                        'token': token.key
                    }, status=status.HTTP_201_CREATED)
                    
                except Exception as e:
                    return Response({
                        'message': f'Error creating user: {str(e)}',
                        'status': 'error'
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            else:
                return Response({
                    'message': message,
                    'status': 'error'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
