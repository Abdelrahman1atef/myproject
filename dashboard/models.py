from django.db import models

class Product(models.Model):
    product_id = models.IntegerField(primary_key=True)  # Use AutoField for auto-incrementing primary key
    product_code = models.CharField(max_length=255, blank=True, null=True)
    product_name_ar = models.CharField(max_length=255, blank=True, null=True)
    product_name_en = models.CharField(max_length=255, blank=True, null=True)
    sell_price = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    group_id = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    company_id = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)

    class Meta:
        db_table = 'products'

    def __str__(self):
        return self.product_name_en
    def save(self, *args, **kwargs):
        # Round the sell_price to 2 decimal places
        if self.sell_price is not None:
            self.sell_price = round(self.sell_price, 2)
        super().save(*args, **kwargs)
