# api/serializers.py
from rest_framework import serializers
from .models import Product

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['product_id', 'product_code', 'product_name_ar', 'product_name_en', 'sell_price','company_id','product_image_url']


def to_representation(self, instance):
        representation = super().to_representation(instance)
        # Ensure no unexpected fields are added
        return {key: representation[key] for key in self.Meta.fields}