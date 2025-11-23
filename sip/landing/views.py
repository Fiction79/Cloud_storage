from django.shortcuts import render

# Create your views here.
# landing/views.py
from django.shortcuts import render

def landing_page(request):
    return render(request, 'landing/index.html')

def pricing_page(request):
    return render(request, 'landing/pricing.html')