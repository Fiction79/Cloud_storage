# clients/views.py
import os
import shutil
import subprocess
from django.shortcuts import render, redirect, get_object_or_404
from django.http import FileResponse, HttpResponse
from django.conf import settings
from django.contrib.auth.decorators import login_required, user_passes_test

from .models import ClientFile, ClientProfile

from django.contrib.auth.models import User
from django.contrib import messages


# -------------------- Admin helpers -------------------- #
def is_admin(user):
    """Check if the user is a superuser (admin)."""
    return user.is_superuser


@user_passes_test(is_admin)
def delete_client(request, user_id):
    """
    Delete a client, their storage folder, and associated DB entries.
    Admin only.
    """
    user = get_object_or_404(ClientProfile, id=user_id)
    storage_path = user.storage_path

    # Delete folder on disk if exists
    if os.path.exists(storage_path):
        shutil.rmtree(storage_path)

    # Delete user and profile
    user.user.delete()  # delete Django User
    user.delete()       # delete ClientProfile

    return redirect('admin_dashboard')  # or another page


# -------------------- Client Dashboard -------------------- #
@login_required
def dashboard(request):
    # Get or create the client profile to ensure it always exists.
    # The default quota here matches the one in the post_save signal.
    client_profile, created = ClientProfile.objects.get_or_create(
        user=request.user,
        defaults={
            'storage_path': os.path.join(settings.USER_DATA_ROOT, request.user.username),
            'quota_limit': 5 * 1024**3  # default 5GB - Matches signal default
        }
    )

    # Ensure storage_path is set correctly if it was just created or was empty
    if not client_profile.storage_path:
        client_profile.storage_path = os.path.join(settings.USER_DATA_ROOT, request.user.username)
        # Only save if quota_limit is also missing (unlikely if get_or_create worked or signal worked)
        if client_profile.quota_limit is None:
             client_profile.quota_limit = 5 * 1024**3 # Or just rely on get_or_create default
        client_profile.save(update_fields=['storage_path']) # Save only the path if it was missing

    # Now ensure the directory exists
    storage_path = client_profile.storage_path
    if storage_path:  # Only try to create if the path is not empty
        os.makedirs(storage_path, exist_ok=True)
    else:
        # This should ideally not happen if get_or_create works correctly,
        # but adding a safeguard. You might want to log this.
        messages.error(request, "Error: Storage path is not configured correctly for your account.")
        # You might want to redirect to an error page or handle this differently
        # For now, we'll render with an empty files list
        return render(request, "clients/dashboard.html", {
            "files": [],
            "used_mb": 0,
            "limit_mb": 0,
            "over_quota": True # Indicate an error state
        })

    files = client_profile.files.all()

    used_bytes = client_profile.used_bytes()
    limit_bytes = client_profile.quota_limit
    over_quota = client_profile.is_over_quota()

    # convert to MB for template
    used_mb = used_bytes / (1024 * 1024)
    limit_mb = limit_bytes / (1024 * 1024)

    return render(request, "clients/dashboard.html", {
        "files": files,
        "used_mb": used_mb,
        "limit_mb": limit_mb,
        "over_quota": over_quota
    })


# -------------------- File Operations -------------------- #
@login_required
def upload_file(request):
    client_profile = ClientProfile.objects.get(user=request.user)
    uploaded_file = request.FILES.get("file")

    # Check if storage_path is valid before proceeding
    if not client_profile.storage_path:
        messages.error(request, "Upload failed: Storage path not configured.")
        return redirect("dashboard")

    if uploaded_file:
        file_size = uploaded_file.size  # in bytes
        if client_profile.used_bytes() + file_size > client_profile.quota_limit:
            messages.error(request, "Upload would exceed your storage quota!")
            return redirect("dashboard")

        # Ensure the directory exists before saving
        user_dir = client_profile.storage_path
        os.makedirs(user_dir, exist_ok=True)
        file_path = os.path.join(user_dir, uploaded_file.name)
        with open(file_path, 'wb+') as dest:
            for chunk in uploaded_file.chunks():
                dest.write(chunk)
        ClientFile.objects.create(client=client_profile, name=uploaded_file.name, size=file_size/(1024*1024))

    return redirect("dashboard")


@login_required
def download_file(request, filename):
    """
    Download a file from the client's storage folder.
    """
    client_profile = ClientProfile.objects.get(user=request.user)
    # Check if storage_path is valid before proceeding
    if not client_profile.storage_path:
        return HttpResponse("File not found: Storage path not configured.", status=404)

    file_path = os.path.join(client_profile.storage_path, filename)
    if os.path.exists(file_path):
        return FileResponse(open(file_path, "rb"), as_attachment=True)
    return HttpResponse("File not found", status=404)


@login_required
def delete_file(request, filename):
    """
    Delete a file from the client's storage folder and DB.
    """
    client_profile = ClientProfile.objects.get(user=request.user)
    # Check if storage_path is valid before proceeding
    if not client_profile.storage_path:
        messages.error(request, "Delete failed: Storage path not configured.")
        return redirect("dashboard")

    file_path = os.path.join(client_profile.storage_path, filename)

    if os.path.exists(file_path):
        os.remove(file_path)

    ClientFile.objects.filter(client=client_profile, name=filename).delete()

    return redirect("dashboard")