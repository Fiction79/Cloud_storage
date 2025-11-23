# clients/urls.py
from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='clients/login.html'), name='login'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('upload/', views.upload_file, name='upload'),
    path('download/<path:filename>/', views.download_file, name='download'),  # Changed to <path:>
    path('delete/<path:filename>/', views.delete_file, name='delete'),  # Changed to <path:>
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('delete-folder/<path:folder_name>/', views.delete_folder, name='delete_folder'),  # Changed to <path:>
    path('folder/<path:folder_name>/', views.folder_view, name='folder_view'),  # NEW
]