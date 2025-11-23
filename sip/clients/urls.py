# clients/urls.py
from django.urls import path
from . import views # Import views from the clients app
from django.contrib.auth import views as auth_views # Import auth views

urlpatterns = [
    # Define the login path
    path('login/', auth_views.LoginView.as_view(template_name='clients/login.html'), name='login'),
    # Define the dashboard path
    path('dashboard/', views.dashboard, name='dashboard'),
    # Define the upload path
    path('upload/', views.upload_file, name='upload'),
    # Define the download path with filename parameter
    path('download/<str:filename>/', views.download_file, name='download'),
    # Define the delete path with filename parameter
    path('delete/<str:filename>/', views.delete_file, name='delete'),
    # Add other client-related paths here if needed
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('delete-folder/<str:folder_name>/', views.delete_folder, name='delete_folder'), 
]