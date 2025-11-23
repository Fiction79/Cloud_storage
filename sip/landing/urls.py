# landing/urls.py
from django.urls import path
from . import views # Import views from the landing app itself

urlpatterns = [
    path('', views.landing_page, name='landing_page'),
    path('pricing/', views.pricing_page, name='pricing_page'),
]
