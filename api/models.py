from django.db import models
from django.contrib.auth.models import AbstractBaseUser
from django.contrib.auth.base_user import BaseUserManager
from django.utils.translation import gettext_lazy as _
from rest_framework.authtoken.models import Token
from django.utils import timezone
from django.core.exceptions import ValidationError

class ProductGroup(models.Model):
    group_id = models.AutoField(primary_key=True)
    group_code = models.CharField(max_length=255, blank=True, null=True)
    group_name_ar=models.CharField(max_length=255, blank=True, null=True)
    group_name_en=models.CharField(max_length=255, blank=True, null=True)
    class Meta:
        managed = False
        db_table = 'Product_groups'

    def __str__(self):
        return self.group_name
    
class Companys(models.Model):
    company_id = models.AutoField(primary_key=True)
    company_code = models.CharField(max_length=255, blank=True, null=True)
    co_name_ar = models.CharField(max_length=255, blank=True, null=True)
    co_name_en = models.CharField(max_length=255, blank=True, null=True)
    class Meta:
        managed = False
        db_table = 'Companys'
    def __str__(self):
        return self.co_name_en

class ProductDescription(models.Model):
    pd_id = models.AutoField(primary_key=True)  # Auto-increment ID
    pd_code = models.CharField(max_length=255, blank=True, null=True)  # Product code
    pd_name_ar = models.TextField(blank=True, null=True)  # Arabic description/name
    pd_name_en = models.TextField(blank=True, null=True)  # English description/name
    deleted = models.BooleanField(default=False)  # Soft delete flag
    insert_date = models.DateTimeField(blank=True, null=True)  # Insert timestamp
    insert_uid = models.CharField(max_length=255, blank=True, null=True)  # User who inserted

    class Meta:
        db_table = 'Product_description'  # Exact name in DB
        managed = False  # Don't let Django manage the table (no migrations)

    def __str__(self):
        return f"{self.pd_code} - {self.pd_name_en or self.pd_name_ar}"    

class ProductAmount(models.Model):
    counter_id = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)  # Add this field
    product_id = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    store_id = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    exp_date = models.DateField(blank=True, null=True)  # Expiry date
    buy_price = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)  # Buy price
    amount = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)  # Stock quantity

    class Meta:
        managed = False
        db_table = 'Product_Amount'
        constraints = [
            models.UniqueConstraint(fields=['product_id', 'store_id', 'counter_id'], name='unique_product_amount')
        ]
    def __str__(self):
         return f"Product ID: {self.product_id}, Store ID: {self.store_id}, Counter ID: {self.counter_id}"

class ProductUnit(models.Model):
    unit_id = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    unit_name_ar = models.CharField(max_length=255, blank=True, null=True)
    unit_name_en = models.CharField(max_length=255, blank=True, null=True)
    class Meta:
        managed = False
        db_table = 'Product_Unit'
    def __str__(self):
        return self.unit_name_en

class Product(models.Model):
    product_id = models.AutoField(primary_key=True)  # Use AutoField for auto-incrementing primary key
    product_code = models.CharField(max_length=255, blank=True, null=True)
    product_name_ar = models.CharField(max_length=255, blank=True, null=True)
    product_name_en = models.CharField(max_length=255, blank=True, null=True)
    company_id = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    sell_price = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    group_id = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    product_image_url = models.URLField(max_length=300,blank=True, null=True)
    product_unit1 = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    product_unit2 = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    product_unit3 = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    product_unit1_2 = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    product_unit1_3 = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    unit2_sell_price = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    unit3_sell_price = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    amount_zero = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    # New fields based on SQL queries
    deleted = models.BooleanField(default=False)  # Indicates if the product is deleted
    active = models.BooleanField(default=True)    # Indicates if the product is active
    product_buy_number = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)  # Buy number
    product_max_disc = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)  # Maximum discount
    product_allow_disc = models.BooleanField(default=True)  # Allow discount flag
    product_made = models.CharField(max_length=255, blank=True, null=True)  # Manufacturer details
    product_minus = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)  # Minus value
    #############################
    class Meta:
        managed = False
        db_table = 'Products'  # Specify the exact table name

    def __str__(self):
        return self.product_name_en

    @property
    def id(self):
        return self.product_id

class ProductCategories(models.Model):
    category_id = models.AutoField(primary_key=True)
    category_name_ar = models.CharField(max_length=255, blank=True, null=True)
    class Meta:
        managed = False
        db_table = 'Product_Categories'
    def __str__(self):
        return self.category_name_ar

class ProductImages(models.Model):
    image_id = models.AutoField(primary_key=True)
    product_id = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    image_url = models.URLField(max_length=300, blank=True, null=True)
    class Meta:
        managed = False
        db_table = 'Product_Images'
    def __str__(self):
        return self.image_url

class AppUserManager(BaseUserManager):
    """
    Custom user model manager where email is the unique identifiers
    for authentication instead of usernames.
    """

    def create_user(self, email=None, phone=None, password=None, **extra_fields):
        """
        Create and save a User with the given email and password.
        """
        if not email and not phone:
            raise ValueError(_('The Email or Phone must be set'))
        
        # Determine whether to use email or phone as the unique identifier
        if email:
            email = self.normalize_email(email)
            user = self.model(email=email, **extra_fields)
        elif phone:
            user = self.model(phone=phone, **extra_fields)
        else:
            raise ValueError(_('Either email or phone must be provided'))

        user.set_password(password)
        user.save(using=self._db)

        # Generate a token for the new user
        Token.objects.create(user=user)

        return user

    def create_superuser(self, email=None, phone=None, password=None, **extra_fields):
        """
        Create and save a SuperUser with the given email and password.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))

        return self.create_user(email=email, phone=phone, password=password, **extra_fields)
    
class AppUser(AbstractBaseUser):
    id = models.AutoField(primary_key=True)  # Align with INT PRIMARY KEY in SQL
    email = models.EmailField(max_length=255, unique=True, null=True, blank=True)  # Changed to EmailField
    phone = models.CharField(max_length=15, unique=True, null=True, blank=True)
    first_name = models.CharField(max_length=255, blank=True, null=True)
    last_name = models.CharField(max_length=255, blank=True, null=True)
    birthdate = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, blank=True, null=True)
    password = models.CharField(max_length=255)
    auth_type = models.CharField(max_length=20, default='phone')
    social_id = models.CharField(max_length=255, blank=True, null=True)
    profile_picture = models.URLField(max_length=500, blank=True, null=True)  # Changed to URLField
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)  # Remove auto_now_add=True
    updated_at = models.DateTimeField(auto_now=True)  # Remove auto_now=True
    last_login = models.DateTimeField(null=True, blank=True)

    objects = AppUserManager()

    USERNAME_FIELD = 'email'  # Alternatively, you can use 'phone' depending on your preference
    REQUIRED_FIELDS = ['phone']

    class Meta:
        managed = False
        db_table = 'app_user'

    def __str__(self):
        return self.email or self.phone  # Return email or phone as the representation
    def update_last_login(self):
        self.last_login = timezone.now()
        self.save(update_fields=['last_login'])

class DeviceToken(models.Model):
    user = models.ForeignKey(AppUser, on_delete=models.CASCADE)
    token = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

class OrderStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    PREPARING = 'preparing', 'Preparing'
    SHIPPED = 'shipped', 'Shipped'
    DELIVERED = 'delivered', 'Delivered'
    CANCELLED = 'cancelled', 'Cancelled'

class App_Order(models.Model):
    user = models.ForeignKey(AppUser, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    total_price = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    status = models.CharField(max_length=50,choices=OrderStatus.choices, default=OrderStatus.PENDING)
    # New fields for location and payment method
    address_name = models.CharField(max_length=255, blank=True, null=True)  # Name/label for the address
    address_street = models.CharField(max_length=500, blank=True, null=True)  # Street address
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    PAYMENT_METHOD_CHOICES = [
        ('cash_on_delivery', 'الدفع عند الاستلام'),
        ('debit_credit_card', 'بطاقة الخصم/الائتمان'),
        ('debit_credit_card_on_delivery', 'بطاقة الخصم/الائتمان عند الاستلام'),
        # ('cash', 'Cash'),
        # ('card', 'Card'),
        # ('other', 'Other'),
    ]
    payment_method = models.CharField(max_length=30, choices=PAYMENT_METHOD_CHOICES, blank=True, null=True)
    # New delivery method fields
    DELIVERY_METHOD_CHOICES = [
        ('home_delivery', 'Home Delivery'),
        ('pharmacy_pickup', 'Pharmacy Pickup'),
    ]
    delivery_method = models.CharField(max_length=20, choices=DELIVERY_METHOD_CHOICES, blank=True, null=True)
    is_home_delivery = models.BooleanField(default=False)
    call_request_enabled = models.BooleanField(default=False)
    promo_code = models.CharField(max_length=50, blank=True, null=True)
    
    def change_status(self, new_status):
        allowed_transitions = {
            OrderStatus.PENDING: [OrderStatus.PREPARING, OrderStatus.CANCELLED],
            OrderStatus.PREPARING: [OrderStatus.SHIPPED, OrderStatus.CANCELLED],
            OrderStatus.SHIPPED: [OrderStatus.DELIVERED],
            OrderStatus.DELIVERED: [],
            OrderStatus.CANCELLED: [],
        }

        if new_status not in allowed_transitions.get(self.status, []):
            raise ValidationError(f"Cannot change status from {self.status} to {new_status}")

        self.status = new_status
        self.save()
    
    def __str__(self):
        return f"Order {self.id} by {self.user.email or self.user.phone}"
    class Meta:
        managed = False
        db_table = 'App_Order'

class App_OrderItem(models.Model):
    order = models.ForeignKey(App_Order, on_delete=models.CASCADE, related_name='items')
    product_id = models.DecimalField(max_digits=18, decimal_places=2)

    # Product snapshot
    product_name_en = models.CharField(max_length=255)
    product_name_ar = models.CharField(max_length=255, null=True, blank=True)

    # Price fields
    sell_price = models.DecimalField(max_digits=18, decimal_places=2)  # Original price per main unit (e.g., box)
    unit_price = models.DecimalField(max_digits=18, decimal_places=2)  # Price based on selected unit

    unit_type = models.CharField(max_length=255)  # e.g., 'Box', 'Strip'
    quantity = models.PositiveIntegerField(default=1)
    item_total = models.DecimalField(max_digits=18, decimal_places=2)

    def save(self, *args, **kwargs):
        self.item_total = self.quantity * self.unit_price
        super().save(*args, **kwargs)

        # Update order total
        order = self.order
        order.total_price = sum(item.item_total for item in order.items.all())
        order.save()

    def __str__(self):
        return f"{self.quantity} x {self.product_name_en}"

    class Meta:
        managed = False
        db_table = 'App_OrderItem'


