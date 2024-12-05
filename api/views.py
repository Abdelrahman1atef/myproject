# # api/views.py

from rest_framework.pagination import PageNumberPagination
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Product
from .serializers import ProductSerializer

class ProductListView(APIView):
    def get(self, request):
        # Query all products from the database
        products = Product.objects.all()

        # Set up pagination
        paginator = PageNumberPagination()
        paginator.page_size = 20  # Set the page size to 10 items per page
        result_page = paginator.paginate_queryset(products, request)

        # Serialize the data
        serializer = ProductSerializer(result_page, many=True)

        # Return paginated data as a JSON response
        return paginator.get_paginated_response(serializer.data)


from django.http import JsonResponse
from django.conf import settings
import requests

def fetch_image_view(request):
    products = Product.objects.all()
    product_name = request.GET.get("product_name_en")
    if not product_name:
        return JsonResponse({"error": "Product name is required"}, status=400)
    
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
        if "items" in data and len(data["items"]) > 0:
            return JsonResponse({"image_url": data["items"][0]["link"]})
        else:
            return JsonResponse({"error": "No image found"}, status=404)
    except requests.exceptions.RequestException as e:
        return JsonResponse({"error": f"Request failed: {str(e)}"}, status=500)
