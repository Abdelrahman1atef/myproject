from django.contrib import admin
from .models import Product

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('product_id', 'product_name_en', 'sell_price', 'company_id', 'group_id')
    list_filter = ('company_id', 'group_id')  # Add filters for easy navigation
    search_fields = ('product_name_en', 'product_code')  # Add search functionality
    ordering = ('product_id',)  # Default ordering

    def save_model(self, request, obj, form, change):
        print(f"Saving product: {obj.product_name_en} new sell_price: {obj.sell_price}")
        super().save_model(request, obj, form, change)