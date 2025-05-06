# api/serializers.py
from rest_framework import serializers
from .models import Product , ProductGroup ,Companys,ProductImages,AppUser,ProductCategories
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
        fields = ['image_id', 'image_url', 'insert_date']

class ProductSerializer(serializers.ModelSerializer):
     product_group = serializers.SerializerMethodField()
     company = serializers.SerializerMethodField()
     product_images = serializers.SerializerMethodField()
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
            'amount',
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
        images = ProductImages.objects.filter(product_id=obj.product_id).order_by('insert_date')
        return ProductImageSerializer(images, many=True).data

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

# class ProductAmountSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = ProductAmount
#         fields = ['product', 'store_id', 'counter_id', 'exp_date', 'buy_price', 'amount']

# class SalesHeaderSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = SalesHeader
#         fields = '__all__'

# class SalesDetailsSerializer(serializers.ModelSerializer):
#     product = ProductSerializer(read_only=True)  # Nested serializer for related product details
#     sales_header = SalesHeaderSerializer(read_only=True)  # Nested serializer for related sale header

#     class Meta:
#         model = SalesDetails
#         fields = '__all__'

# class GedoFinancialSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = GedoFinancial
#         fields = '__all__'

# class CashDepotsSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = CashDepots
#         fields = '__all__'    


# def to_representation(self, instance):
#         representation = super().to_representation(instance)
#         # Ensure no unexpected fields are added
#         return {key: representation[key] for key in self.Meta.fields}

