# sip/urls.py
from django.contrib import admin
from django.urls import path, include # Import include
from django.shortcuts import redirect

urlpatterns = [
    # Option 1: If you want / to directly show the landing page content (requires landing/urls.py to have path('', ...))
    # In this case, remove the redirect from here and let landing handle the root.
    # path('', include('landing.urls')), # This includes landing's path('', views.landing_page, name='landing_page')

    # Option 2: If you want / to redirect to a specific landing page URL (e.g., /landing/)
    path('', lambda request: redirect('landing_page')), # Redirect root to the named URL 'landing_page'
    # Include the landing app's URLs under the 'landing/' prefix
    path('landing/', include('landing.urls')), # This looks for landing/urls.py
    # Include the clients app's URLs (handles login, dashboard, etc.)
    # This catches other paths like /login/, /dashboard/ that don't match /landing/ or /admin/
    path('', include('clients.urls')), # This looks for clients/urls.py
    # Keep the admin URLs
    path('admin/', admin.site.urls),
]