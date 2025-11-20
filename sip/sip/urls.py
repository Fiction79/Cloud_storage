from django.contrib import admin
from django.urls import path
from clients import views
from django.contrib.auth import views as auth_views
from django.shortcuts import redirect

urlpatterns = [
    path('', lambda request: redirect('login')),
    path('admin/', admin.site.urls),
    path('login/', auth_views.LoginView.as_view(template_name='clients/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('upload/', views.upload_file, name='upload'),
    path('download/<str:filename>/', views.download_file, name='download'),
    path('delete/<str:filename>/', views.delete_file, name='delete'),
]
