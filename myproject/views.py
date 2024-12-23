from django.shortcuts import render

# Create a simple view for the root URL
def index(request):
    return render(request, 'index.html')  # Render index.html template
