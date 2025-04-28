from django.db import models
from django.contrib.auth.models import AbstractBaseUser
from django.contrib.auth.base_user import BaseUserManager
from django.utils.translation import gettext_lazy as _
from rest_framework.authtoken.models import Token
from django.utils import timezone

class ProductGroup(models.Model):
    group_id = models.AutoField(primary_key=True)
    group_code = models.CharField(max_length=255, blank=True, null=True)
    group_name_ar=models.CharField(max_length=255, blank=True, null=True)
    group_name_en=models.CharField(max_length=255, blank=True, null=True)
    class Meta:
        db_table = 'Product_groups'

    def __str__(self):
        return self.group_name
    
class Companys(models.Model):
    company_id = models.AutoField(primary_key=True)
    company_code = models.CharField(max_length=255, blank=True, null=True)
    co_name_ar = models.CharField(max_length=255, blank=True, null=True)
    co_name_en = models.CharField(max_length=255, blank=True, null=True)
    class Meta:
        db_table = 'Companys'
    def __str__(self):
        return self.co_name_en
    
class ProductAmount(models.Model):
    counter_id = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)  # Add this field
    product_id = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    store_id = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    exp_date = models.DateField(blank=True, null=True)  # Expiry date
    buy_price = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)  # Buy price
    amount = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)  # Stock quantity

    class Meta:
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
        db_table = 'Products'  # Specify the exact table name

    def __str__(self):
        return self.product_name_en

class ProductCategories(models.Model):
    category_id = models.AutoField(primary_key=True)
    category_name_ar = models.CharField(max_length=255, blank=True, null=True)
    class Meta:
        db_table = 'Product_Categories'
    def __str__(self):
        return self.category_name_ar

class ProductImages(models.Model):
    image_id = models.AutoField(primary_key=True)
    product_id = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    image_url = models.URLField(max_length=300, blank=True, null=True)
    class Meta:
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
        db_table = 'app_user'

    def __str__(self):
        return self.email or self.phone  # Return email or phone as the representation
    def update_last_login(self):
        self.last_login = timezone.now()
        self.save(update_fields=['last_login'])
#######################################################################
# class SalesHeader(models.Model):
#     sales_id = models.AutoField(primary_key=True)
#     store_id = models.IntegerField(blank=True, null=True)  # Updated from DecimalField to IntegerField
#     customer_id = models.IntegerField(blank=True, null=True)  # Updated from DecimalField to IntegerField
#     class_type = models.CharField(max_length=1, db_column='class', blank=True, null=True)  # Map to 'class' column
#     product_number = models.IntegerField(blank=True, null=True)  # Number of products in the sale
#     bill_money_befor = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)  # Bill before discount
#     total_bill = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)  # Total bill
#     total_after_disc = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)  # Total after discount
#     total_bill_net = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)  # Net total bill
#     total_disc_per = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)  # Discount percentage
#     total_disc_money = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)  # Discount amount
#     total_product_disc = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)  # Product discount
#     total_product_disc = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)  # Product discount percentage
#     cashier_id = models.CharField(max_length=255, blank=True, null=True)  # Cashier ID
#     notes = models.TextField(blank=True, null=True)  # Notes
#     bill_other_expenses = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)  # Other expenses
#     bill_cash = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)  # Cash received
#     gf_id = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)  # Financial transaction ID
#     compu_name = models.CharField(max_length=255, blank=True, null=True)  # Computer name
#     cashier_disk_id = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)  # Cashier disk ID
#     insert_uid = models.CharField(max_length=255, blank=True, null=True)  # Insert user ID
#     sale_class = models.IntegerField(blank=True, null=True)  # Sale class (e.g., 0 for normal sale)
#     money_change = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)  # Change given
#     network_money = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)  # Network money
#     network_id = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)  # Network ID

#     class Meta:
#         db_table = 'Sales_header'

#     def __str__(self):
#         return f"Sale #{self.sales_id}"

# class SalesDetails(models.Model):
#     details_id = models.IntegerField(blank=True, null=True)  # Line item number (not globally unique)
#     sales = models.ForeignKey(SalesHeader, on_delete=models.CASCADE, related_name="details")  # Relationship with SalesHeader
#     product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="sales_details")  # Relationship with Product
#     counter_id = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
#     exp_date = models.DateField(blank=True, null=True)  # Expiry date
#     amount = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)  # Quantity sold
#     sale_unit_change = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)  # Unit change
#     sale_unit = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)  # Sale unit
#     sell_price = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)  # Sell price
#     buy_price = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)  # Buy price
#     disc_money = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)  # Discount amount
#     disc_per = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)  # Discount percentage
#     total_sell = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)  # Total sell price
#     back = models.BooleanField(default=False)  # Indicates if the item was returned
#     back_amount = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)  # Return amount
#     back_unit_change = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)  # Return unit change
#     back_price = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)  # Return price
#     back_unit = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)  # Return unit
#     back_gf_id = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)  # Return financial transaction ID

#     class Meta:
#         db_table = 'Sales_details'
#         unique_together = ('sales', 'details_id')  # Ensure uniqueness of (sales_id, details_id)

#     def __str__(self):
#         return f"Detail #{self.details_id} - {self.product}"

# class GedoFinancial(models.Model):
#     gf_id = models.AutoField(primary_key=True)
#     gf_gedo_type = models.IntegerField(blank=True, null=True)  # Type of financial transaction
#     gf_value = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)  # Transaction value
#     gf_from_type = models.IntegerField(blank=True, null=True)  # From type
#     gf_from_id = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)  # From ID
#     gf_to_type = models.IntegerField(blank=True, null=True)  # To type
#     gf_to_id = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)  # To ID
#     gf_notes = models.CharField(max_length=255, blank=True, null=True)  # Notes
#     gf_computer = models.CharField(max_length=255, blank=True, null=True)  # Computer name
#     gf_actual_cashier = models.CharField(max_length=255, blank=True, null=True)  # Actual cashier
#     gf_form_type = models.IntegerField(blank=True, null=True)  # Form type
#     insert_uid = models.CharField(max_length=255, blank=True, null=True)  # Insert user ID
#     insert_date = models.DateTimeField(auto_now_add=True)  # Insert date

#     class Meta:
#         db_table = 'Gedo_Financial'

#     def __str__(self):
#         return f"Financial #{self.gf_id}"

# class CashDepots(models.Model):
#     cash_depot_code = models.CharField(max_length=255, blank=True, null=True)
#     cash_depot_name_ar = models.CharField(max_length=255, blank=True, null=True)
#     cash_depot_name_en = models.CharField(max_length=255, blank=True, null=True)
#     cash_depot_class = models.CharField(max_length=255, blank=True, null=True)
#     cash_depot_current_money = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)  # Current cash balance
#     update_uid = models.CharField(max_length=255, blank=True, null=True)  # Update user ID
#     update_date = models.DateTimeField(auto_now=True)  # Last updated date

#     class Meta:
#         db_table = 'Cash_depots'

#     def __str__(self):
#         return self.cash_depot_name_en


