# clients/admin.py
from django.contrib import admin
from .models import ClientProfile, ClientFile
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

# Remove the ClientProfileInline class definition if it exists,
# or just don't include it in the UserAdmin.inlines list below.

# Define UserAdmin without the inline
class UserAdmin(BaseUserAdmin):
    # inlines = (ClientProfileInline,) # Remove this line or comment it out
    inlines = () # Explicitly set to empty tuple if the inline was previously defined

# Unregister the default User admin
admin.site.unregister(User)
# Register User again with our modified UserAdmin (which now has no inline)
admin.site.register(User, UserAdmin)

# Keep registering ClientProfile and ClientFile separately
admin.site.register(ClientProfile)
admin.site.register(ClientFile)
