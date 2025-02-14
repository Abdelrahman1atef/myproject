# api/serializers.py
from rest_framework import serializers
from .models import Product , ProductGroup ,Companys

class ProductGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductGroup
        fields = ['group_id', 'group_name_en', 'group_name_ar']
    
class CompanysSerializer(serializers.ModelSerializer):
    class Meta:
        model = Companys
        fields = ['company_id', 'co_name_en', 'co_name_ar']

class ProductSerializer(serializers.ModelSerializer):
     product_group = serializers.SerializerMethodField()
     company = serializers.SerializerMethodField()
     class Meta:
        model = Product
        fields = [
            'product_id',
            'product_code',
            'product_name_ar',
            'product_name_en',
            'sell_price',
            'product_image_url',
            'company',
            'product_group',
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
def to_representation(self, instance):
        representation = super().to_representation(instance)
        # Ensure no unexpected fields are added
        return {key: representation[key] for key in self.Meta.fields}

