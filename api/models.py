from django.db import models


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
    product_id = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    amount = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    class Meta:
        db_table = 'Product_Amount'
    def __str__(self):
        return self.amount

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
#######################################################################
class SalesHeader(models.Model):
    sales_id = models.AutoField(primary_key=True)
    store_id = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    customer_id = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    class_type = models.CharField(max_length=1, blank=True, null=True)  # Class type (e.g., '0' for normal sale)
    product_number = models.IntegerField(blank=True, null=True)  # Number of products in the sale
    bill_money_befor = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)  # Bill before discount
    total_bill = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)  # Total bill
    total_after_disc = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)  # Total after discount
    total_bill_net = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)  # Net total bill
    total_disc_per = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)  # Discount percentage
    total_disc_money = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)  # Discount amount
    cashier_id = models.CharField(max_length=255, blank=True, null=True)  # Cashier ID
    notes = models.TextField(blank=True, null=True)  # Notes
    bill_other_expenses = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)  # Other expenses
    bill_cash = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)  # Cash received
    gf_id = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)  # Financial transaction ID
    compu_name = models.CharField(max_length=255, blank=True, null=True)  # Computer name
    cashier_disk_id = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)  # Cashier disk ID
    insert_uid = models.CharField(max_length=255, blank=True, null=True)  # Insert user ID
    sale_class = models.IntegerField(blank=True, null=True)  # Sale class (e.g., 0 for normal sale)
    money_change = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)  # Change given
    network_money = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)  # Network money
    network_id = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)  # Network ID

    class Meta:
        db_table = 'Sales_header'

    def __str__(self):
        return f"Sale #{self.sales_id}"

class SalesDetails(models.Model):
    details_id = models.AutoField(primary_key=True)
    sales = models.ForeignKey(SalesHeader, on_delete=models.CASCADE, related_name="details")  # Relationship with SalesHeader
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="sales_details")  # Relationship with Product
    counter_id = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    exp_date = models.DateField(blank=True, null=True)  # Expiry date
    amount = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)  # Quantity sold
    sale_unit_change = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)  # Unit change
    sale_unit = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)  # Sale unit
    sell_price = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)  # Sell price
    buy_price = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)  # Buy price
    disc_money = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)  # Discount amount
    disc_per = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)  # Discount percentage
    total_sell = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)  # Total sell price
    back = models.BooleanField(default=False)  # Indicates if the item was returned
    back_amount = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)  # Return amount
    back_unit_change = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)  # Return unit change
    back_price = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)  # Return price
    back_unit = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)  # Return unit
    back_gf_id = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)  # Return financial transaction ID

    class Meta:
        db_table = 'Sales_details'

    def __str__(self):
        return f"Detail #{self.details_id} - {self.product}"

class GedoFinancial(models.Model):
    gf_id = models.AutoField(primary_key=True)
    gf_gedo_type = models.IntegerField(blank=True, null=True)  # Type of financial transaction
    gf_value = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)  # Transaction value
    gf_from_type = models.IntegerField(blank=True, null=True)  # From type
    gf_from_id = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)  # From ID
    gf_to_type = models.IntegerField(blank=True, null=True)  # To type
    gf_to_id = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)  # To ID
    gf_notes = models.CharField(max_length=255, blank=True, null=True)  # Notes
    gf_computer = models.CharField(max_length=255, blank=True, null=True)  # Computer name
    gf_actual_cashier = models.CharField(max_length=255, blank=True, null=True)  # Actual cashier
    gf_form_type = models.IntegerField(blank=True, null=True)  # Form type
    insert_uid = models.CharField(max_length=255, blank=True, null=True)  # Insert user ID
    insert_date = models.DateTimeField(auto_now_add=True)  # Insert date

    class Meta:
        db_table = 'Gedo_Financial'

    def __str__(self):
        return f"Financial #{self.gf_id}"

class CashDepots(models.Model):
    cash_depot_code = models.CharField(max_length=255, blank=True, null=True)
    cash_depot_name_ar = models.CharField(max_length=255, blank=True, null=True)
    cash_depot_name_en = models.CharField(max_length=255, blank=True, null=True)
    cash_depot_class = models.CharField(max_length=255, blank=True, null=True)
    cash_depot_current_money = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)  # Current cash balance
    update_uid = models.CharField(max_length=255, blank=True, null=True)  # Update user ID
    update_date = models.DateTimeField(auto_now=True)  # Last updated date

    class Meta:
        db_table = 'Cash_depots'

    def __str__(self):
        return self.cash_depot_name_en


