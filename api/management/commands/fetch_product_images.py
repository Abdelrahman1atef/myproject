from django.core.management.base import BaseCommand
import requests
from api.models import Product  # Adjust according to your models
from django.conf import settings

class Command(BaseCommand):
    help = "Fetch product images using Google CSE"

    def fetch_image(self, product_name):
        api_url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "q": product_name,
            "cx": settings.GOOGLE_CX,
            "key": settings.GOOGLE_API_KEY,
            "searchType": "image",
            "num": 1,
        }
        try:
             response = requests.get(api_url, params=params)
             response.raise_for_status()  # Raises an error for bad responses
             data = response.json()
             if "items" in data:
                 print()
                 return data["items"][0]["link"]
        except requests.exceptions.RequestException as e:
                 self.stdout.write(f"Error fetching image for {product_name}: {str(e)}")
                 return None

    def handle(self, *args, **options):
        products = Product.objects.all()
        for product in products:
            image_url = self.fetch_image(product.product_name_en)
            if image_url:
                product.image_url = image_url
                self.stdout.write(f"Saving product: {product.product_name_en}, Image URL: {product.image_url}")
                # product.product_image_url.save()
                self.stdout.write(f"Updated {product.product_name_en} with image URL.")
            else:
                self.stdout.write(f"No image found for {product.product_name_en}.")
