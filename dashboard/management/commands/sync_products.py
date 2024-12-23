import requests
from django.core.management.base import BaseCommand
from dashboard.models import Product

class Command(BaseCommand):
    help = 'Sync products from API'

    def handle(self, *args, **kwargs):
        url = "http://127.0.0.1:8000/api/allproducts/"
        while url:
            response = requests.get(url)
            data = response.json()
            for item in data['results']:
                Product.objects.update_or_create(
                    product_id=item['product_id'],
                    defaults={
                        'product_code': item['product_code'],
                        'product_name_ar': item['product_name_ar'],
                        'product_name_en': item['product_name_en'],
                        'sell_price': item['sell_price'],
                        'company_id': item['company_id'],
                        'group_id': item['group_id'],
                    },
                )
            url = data.get('next')  # Handle pagination
        self.stdout.write(self.style.SUCCESS("Products synced successfully!"))
