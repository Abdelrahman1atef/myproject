# api/serializers.py
from decimal import Decimal
from rest_framework import serializers
from .models import Product , ProductGroup ,Companys,ProductImages,AppUser,ProductCategories,App_Order, App_OrderItem
from .models import ProductAmount,ProductDescription,DeviceToken
from django.contrib.auth.hashers import make_password
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from django.core.exceptions import ValidationError

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductCategories
        fields = ['category_id','category_name_ar']

class ProductGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductGroup
        fields = ['group_id', 'group_name_en', 'group_name_ar']
    
class CompanysSerializer(serializers.ModelSerializer):
    class Meta:
        model = Companys
        fields = ['company_id', 'co_name_en', 'co_name_ar']

class ProductImageSerializer(serializers.ModelSerializer):
    """Serializer for product images."""
    class Meta:
        model = ProductImages
        fields = ['image_id', 'image_url']

class ProductSerializer(serializers.ModelSerializer):
     product_group = serializers.SerializerMethodField()
     company = serializers.SerializerMethodField()
     product_images = serializers.SerializerMethodField()
     stock_amount = serializers.SerializerMethodField()
     product_description = serializers.SerializerMethodField()
     class Meta:
        model = Product
        fields = [
            'product_id',
            'product_code',
            'product_name_ar',
            'product_name_en',
            'product_unit1',
            'sell_price',
            'product_unit2',
            'unit2_sell_price',
            'product_unit3',
            'unit3_sell_price',
            'stock_amount',
            'product_image_url',
            'product_description',
            'company',
            'product_group',
            'product_images',
            ]
     def get_product_group(self, obj):
        # Fetch the ProductGroup using group_id
        if obj.group_id:
            try:
                product_group = ProductGroup.objects.get(group_id=obj.group_id)
                return {
                    "group_id": product_group.group_id,
                    "group_name_en": product_group.group_name_en,
                    "group_name_ar": product_group.group_name_ar
                }
            except ProductGroup.DoesNotExist:
                return None
        return None
     def get_company(self, obj):
        # Fetch the Companys using company_id
        if obj.company_id:
            try:
                company = Companys.objects.get(company_id=obj.company_id)
                return {
                    "company_id": company.company_id,
                    "co_name_en": company.co_name_en,
                    "co_name_ar": company.co_name_ar
                }
            except Companys.DoesNotExist:
                return None
        return None
     def get_product_images(self, obj):
        """Fetch all images associated with the product."""
        images = ProductImages.objects.filter(product_id=obj.product_id)
        return ProductImageSerializer(images, many=True).data
     def get_stock_amount(self, obj):
        """Get amount from ProductAmount table based on product_id"""
        try:
            # Get latest available amount (you can customize logic)
            product_amount = ProductAmount.objects.filter(product_id=obj.product_id).latest('counter_id')
            return product_amount.amount
        except ProductAmount.DoesNotExist:
            return 0
     def get_product_description(self, obj):
        try:
            desc = ProductDescription.objects.get(pd_code=obj.product_code, deleted=False)
            return desc.pd_name_en or desc.pd_name_ar or "No description available"
        except ProductDescription.DoesNotExist:
            return "No description available"  

class ProductSearchSerializer(serializers.ModelSerializer):
    sell_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    class Meta:
        model = Product
        fields = [
            'product_id',
            'product_name_ar',
            'product_name_en',
            'sell_price',
            'product_image_url',
            ]
    def get_product_group(self, obj):
        # Fetch the ProductGroup using group_id
        if obj.group_id:
            try:
                product_group = ProductGroup.objects.get(group_id=obj.group_id)
                return {
                    "group_id": product_group.group_id,
                    "group_name_en": product_group.group_name_en,
                    "group_name_ar": product_group.group_name_ar
                }
            except ProductGroup.DoesNotExist:
                return None
        return None

    def get_company(self, obj):
        # Fetch the Companys using company_id
        if obj.company_id:
            try:
                company = Companys.objects.get(company_id=obj.company_id)
                return {
                    "company_id": company.company_id,
                    "co_name_en": company.co_name_en,
                    "co_name_ar": company.co_name_ar
                }
            except Companys.DoesNotExist:
                return None
        return None

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppUser
        fields = [
            'id',
            'email',
            'phone',
            'first_name',
            'last_name',
            'birthdate',
            'gender',
            'auth_type',
            'social_id',
            'profile_picture',
            'is_active',
            'is_staff',
            'created_at',
            'updated_at',
            'last_login',
        ]

class AppUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})

    class Meta:
        model = AppUser
        fields = (
            'email',
            'phone',
            'first_name',
            'last_name',
            'birthdate',
            'gender',
            'password',
            'auth_type',
            'social_id',
            'profile_picture',
            'is_active',
            'is_staff',
            'last_login')
        extra_kwargs = {
            'id': {'read_only': True},
            'created_at': {'read_only': True},
            'updated_at': {'read_only': True},
        }

    def validate_email(self, value):
        if value and AppUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate_phone(self, value):
        if value and AppUser.objects.filter(phone=value).exists():
            raise serializers.ValidationError("A user with this phone number already exists.")
        return value

    def create(self, validated_data):
        validated_data['password'] = make_password(validated_data['password'])
        return super().create(validated_data)

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False, allow_null=True)
    phone = serializers.CharField(required=False, allow_null=True)
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})

    def validate(self, data):
        email = data.get('email')
        phone = data.get('phone')
        password = data.get('password')
    
        # Validate inputs
        if not email and not phone:
            raise ValidationError("Either email or phone number is required.")
        if not password:
            raise ValidationError("Password is required.")

        # Find user by email or phone
        user = None
        if email:
            try:
                user = AppUser.objects.get(email=email)
            except AppUser.DoesNotExist:
                raise ValidationError("Invalid email/phone or password.")
        elif phone:
            try:
                user = AppUser.objects.get(phone=phone)
            except AppUser.DoesNotExist:
                raise ValidationError("Invalid email/phone or password.")

        # Authenticate user
        if not user or not authenticate(username=email or user.email, password=password):
            raise ValidationError("Invalid email/phone or password.")

        # Check if user is active
        if not user.is_active:
            raise ValidationError("This account is inactive.")

        # Update last login
        user.update_last_login()

        # Get or create token
        token, created = Token.objects.get_or_create(user=user)

        return {
            'token': token.key,
            'user': self.user_to_dict(user)
        }

    def user_to_dict(self, user):
        return {
            'id': user.id,
            'email': user.email,
            'phone':user.phone,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'birthdate': user.birthdate,
            'gender': user.gender,
            'auth_type': user.auth_type,
            'social_id': user.social_id,
            'profile_picture': user.profile_picture,
            'is_active': user.is_active,
            'is_staff': user.is_staff,
            'last_login': user.last_login
        }

class DeviceTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceToken
        fields = ['token']

class OrderItemSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    product_name_ar = serializers.CharField()
    product_name_en = serializers.CharField()
    product_unit1 = serializers.CharField()
    sell_price = serializers.FloatField()
    product_unit2 = serializers.CharField()
    product_unit1_2 = serializers.FloatField()
    unit2_sell_price = serializers.FloatField()
    product_images = serializers.ListField(child=serializers.URLField(), required=False)
    quantity = serializers.IntegerField(min_value=1)

class OrderCreateSerializer(serializers.Serializer):
    user_id = serializers.IntegerField(required=True)
    products = serializers.ListField(child=serializers.DictField())  # More flexible than OrderItemSerializer

    def validate_user_id(self, value):
        request = self.context.get('request')
        if not request or value != request.user.id:
            raise serializers.ValidationError("User ID does not match authenticated user")
        return value

    def validate(self, data):
        # Ensure all products have required fields
        for product in data['products']:
            if 'product_id' not in product or 'quantity' not in product:
                raise serializers.ValidationError("Each product must contain product_id and quantity")
        return data

    def create(self, validated_data):
        user = self.context['request'].user
        products_data = validated_data['products']
        
        order = App_Order.objects.create(user=user)
        total_order_price = Decimal('0')

        for product_data in products_data:
            try:
                # Get fresh product data from database (don't trust client data)
                product = Product.objects.get(product_id=product_data['product_id'])
            except Product.DoesNotExist:
                raise serializers.ValidationError(f"Product {product_data['product_id']} not found")

            quantity = Decimal(str(product_data['quantity']))
            
            # Use server-side calculated price, not client-provided price
            unit_type = product_data.get('selected_unit', 'product_unit1')
            if unit_type == 'product_unit2':
                unit_price = product.unit2_sell_price
            elif unit_type == 'product_unit3':
                unit_price = product.unit3_sell_price
            else:
                unit_price = product.sell_price

            item_total = unit_price * quantity

            App_OrderItem.objects.create(
                order=order,
                product_id=product.product_id,
                product_name_en=product.product_name_en,  # From DB, not request
                product_name_ar=product.product_name_ar,    # From DB, not request
                sell_price=product.sell_price,
                unit_type=getattr(product, unit_type, 'Unknown'),
                unit_price=unit_price,
                quantity=quantity,
                item_total=item_total
            )

            total_order_price += item_total

        order.total_price = total_order_price
        order.save()
        return order

class OrderItemListSerializer(serializers.ModelSerializer):
    product_images = serializers.SerializerMethodField()
    class Meta:
        model = App_OrderItem
        fields = [
            'product_id',
            'product_name_en',
            'product_name_ar',
            'sell_price',
            'unit_price',
            'unit_type',
            'quantity',
            'item_total',
            'product_images',
        ]

    def get_product_images(self, obj):
        """Fetch all images associated with the product."""
        images = ProductImages.objects.filter(product_id=obj.product_id)
        return [img.image_url for img in images]

class OrderListSerializer(serializers.ModelSerializer):
    items = OrderItemListSerializer(many=True, read_only=True)
    first_name = serializers.SerializerMethodField()
    last_name = serializers.SerializerMethodField()
    user_email = serializers.SerializerMethodField()
    user_phone = serializers.SerializerMethodField()

    class Meta:
        model = App_Order
        fields = [
            'id',
            'user_id',
            'first_name',
            'last_name',
            'user_email',
            'user_phone',
            'created_at',
            'total_price',
            'status',
            'items',
        ]
    def get_first_name(self, obj):
        return obj.user.first_name

    def get_last_name(self, obj):
        return obj.user.last_name

    def get_user_email(self, obj):
        return obj.user.email

    def get_user_phone(self, obj):
        return obj.user.phone

class CustomerOrderListSerializer(serializers.ModelSerializer):
    items = OrderItemListSerializer(many=True, read_only=True)
    
    class Meta:
        model = App_Order
        fields = [
            'id',
            'created_at',
            'total_price',
            'status',
            'items',
        ]
        # Removed user-specific fields since customer already knows their own info

class OrderStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = App_Order
        fields = ['status']



