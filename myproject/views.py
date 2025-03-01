from django.shortcuts import render
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
# Create a simple view for the root URL
def index(request):
    return render(request, 'index.html')  # Render index.html template

   

def custom_404(request, exception):
    status_code = 404
    return JsonResponse({
        'status': 'error',
        'status_code':status_code,
        'message': 'Not found',
    }, status=status_code)

