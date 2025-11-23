import os
import shutil
from django.shortcuts import render, redirect, get_object_or_404
from django.http import FileResponse, HttpResponse
from django.conf import settings
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth.models import User

from urllib.parse import unquote

from .models import ClientFile, ClientProfile
from django.db.models import Q


# -------------------- Admin helpers -------------------- #
def is_admin(user):
    return user.is_superuser


@user_passes_test(is_admin)
def delete_client(request, user_id):
    user_profile = get_object_or_404(ClientProfile, id=user_id)
    storage_path = user_profile.storage_path

    if os.path.exists(storage_path):
        shutil.rmtree(storage_path)

    user_profile.user.delete()
    user_profile.delete()

    return redirect('admin_dashboard')


# -------------------- Client Dashboard -------------------- #
@login_required
def dashboard(request):
    client_profile, created = ClientProfile.objects.get_or_create(
        user=request.user,
        defaults={
            'storage_path': os.path.join(settings.USER_DATA_ROOT, request.user.username),
            'quota_limit': 5 * 1024**3
        }
    )

    if not client_profile.storage_path:
        client_profile.storage_path = os.path.join(settings.USER_DATA_ROOT, request.user.username)
        if client_profile.quota_limit is None:
            client_profile.quota_limit = 5 * 1024**3
        client_profile.save(update_fields=['storage_path'])

    storage_path = client_profile.storage_path
    if not storage_path:
        messages.error(request, "Error: Storage path is not configured correctly.")
        return render(request, "clients/dashboard.html", {
            "files": [], "folders": [], "used_mb": 0, "limit_mb": 0, "over_quota": True
        })

    os.makedirs(storage_path, exist_ok=True)

    # Group files into folders and standalone
    all_files = client_profile.files.all()
    folders_dict = {}
    standalone_files = []

    for f in all_files:
        if f.relative_path and '/' in f.relative_path:
            top_folder = f.relative_path.split('/')[0]
            if top_folder not in folders_dict:
                folders_dict[top_folder] = {
                    'name': top_folder,
                    'file_count': 0,
                    'uploaded_at': f.uploaded_at
                }
            folders_dict[top_folder]['file_count'] += 1
        else:
            standalone_files.append(f)

    folder_list = list(folders_dict.values())

    used_bytes = client_profile.used_bytes()
    limit_bytes = client_profile.quota_limit
    over_quota = client_profile.is_over_quota()
    used_mb = used_bytes / (1024 * 1024)
    limit_mb = limit_bytes / (1024 * 1024)

    return render(request, "clients/dashboard.html", {
        "files": standalone_files,
        "folders": folder_list,
        "used_mb": used_mb,
        "limit_mb": limit_mb,
        "over_quota": over_quota
    })


# -------------------- NEW: Folder View -------------------- #
@login_required
def folder_view(request, folder_name):
    client_profile = ClientProfile.objects.get(user=request.user)
    
    # Get all files in this folder
    files_in_folder = client_profile.files.filter(
        relative_path__startswith=folder_name + '/'
    )
    
    # Organize into subfolders and files
    subfolders_dict = {}
    direct_files = []
    
    for f in files_in_folder:
        # Remove the parent folder name from the path
        remaining_path = f.relative_path[len(folder_name) + 1:]
        
        if '/' in remaining_path:
            # This file is in a subfolder
            subfolder_name = remaining_path.split('/')[0]
            if subfolder_name not in subfolders_dict:
                subfolders_dict[subfolder_name] = {
                    'name': subfolder_name,
                    'full_path': folder_name + '/' + subfolder_name,
                    'file_count': 0,
                    'uploaded_at': f.uploaded_at
                }
            subfolders_dict[subfolder_name]['file_count'] += 1
        else:
            # This file is directly in the current folder
            direct_files.append(f)
    
    subfolder_list = list(subfolders_dict.values())
    
    # Calculate quota
    used_bytes = client_profile.used_bytes()
    limit_bytes = client_profile.quota_limit
    over_quota = client_profile.is_over_quota()
    used_mb = used_bytes / (1024 * 1024)
    limit_mb = limit_bytes / (1024 * 1024)
    
    return render(request, "clients/folder_view.html", {
        "folder_name": folder_name,
        "files": direct_files,
        "subfolders": subfolder_list,
        "used_mb": used_mb,
        "limit_mb": limit_mb,
        "over_quota": over_quota
    })


# -------------------- File Operations -------------------- #
@login_required
def upload_file(request):
    if request.method != "POST":
        return redirect("dashboard")

    client_profile = ClientProfile.objects.get(user=request.user)

    if not client_profile.storage_path:
        messages.error(request, "Upload failed: Storage path not configured.")
        return redirect("dashboard")

    uploaded_files = request.FILES.getlist("files")
    file_paths = request.POST.getlist("file_paths[]")
    
    if not uploaded_files:
        messages.warning(request, "No files were selected.")
        return redirect("dashboard")
    
    # Debug
    print(f"DEBUG: Number of files: {len(uploaded_files)}")
    print(f"DEBUG: Number of paths: {len(file_paths)}")
    for i, (f, p) in enumerate(zip(uploaded_files, file_paths)):
        print(f"DEBUG: File {i}: {f.name} -> Path: {p}")

    total_size = sum(f.size for f in uploaded_files)
    if client_profile.used_bytes() + total_size > client_profile.quota_limit:
        messages.error(request, "Upload would exceed your storage quota!")
        return redirect("dashboard")

    user_dir = client_profile.storage_path
    os.makedirs(user_dir, exist_ok=True)

    for i, uploaded_file in enumerate(uploaded_files):
        # Get the relative path from the separate field
        if i < len(file_paths):
            relative_path = file_paths[i]
        else:
            # Fallback to filename if path not provided
            relative_path = uploaded_file.name
        
        # Debug: print what we're receiving
        print(f"DEBUG: Processing file {i}: {uploaded_file.name} as path: {relative_path}")

        # SECURITY: Normalize and prevent directory traversal
        relative_path = os.path.normpath(relative_path)
        if relative_path.startswith("..") or os.path.isabs(relative_path) or '\0' in relative_path:
            messages.error(request, f"Invalid file path: {relative_path}")
            continue

        full_path = os.path.join(user_dir, relative_path)
        
        # Create directories if they don't exist
        file_dir = os.path.dirname(full_path)
        if file_dir:  # Only create if there's a directory path
            os.makedirs(file_dir, exist_ok=True)

        with open(full_path, 'wb+') as dest:
            for chunk in uploaded_file.chunks():
                dest.write(chunk)

        ClientFile.objects.create(
            client=client_profile,
            name=os.path.basename(relative_path),
            relative_path=relative_path,
            size=uploaded_file.size / (1024 * 1024)
        )

    messages.success(request, f"{len(uploaded_files)} file(s) uploaded successfully!")
    return redirect("dashboard")


@login_required
def download_file(request, filename):
    client_profile = ClientProfile.objects.get(user=request.user)
    if not client_profile.storage_path:
        return HttpResponse("Storage not configured.", status=404)

    # Decode the filename (it may contain URL encoding)
    filename = unquote(filename)
    
    file_path = os.path.join(client_profile.storage_path, filename)
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return FileResponse(open(file_path, "rb"), as_attachment=True)
    return HttpResponse("File not found", status=404)


@login_required
def delete_file(request, filename):
    client_profile = ClientProfile.objects.get(user=request.user)
    if not client_profile.storage_path:
        messages.error(request, "Delete failed: Storage path not configured.")
        return redirect("dashboard")

    # Decode the filename
    filename = unquote(filename)
    
    # Check if this is a file inside a folder
    is_nested = '/' in filename
    
    # Delete from DB
    ClientFile.objects.filter(
        client=client_profile
    ).filter(
        Q(name=filename) | Q(relative_path=filename)
    ).delete()

    # Delete from disk
    file_path = os.path.join(client_profile.storage_path, filename)
    if os.path.exists(file_path):
        if os.path.isdir(file_path):
            shutil.rmtree(file_path)
        else:
            os.remove(file_path)

    # Redirect back to folder view if it was a nested file
    if is_nested:
        folder_name = filename.split('/')[0]
        messages.success(request, f"File deleted successfully!")
        return redirect('folder_view', folder_name=folder_name)
    
    return redirect("dashboard")


@login_required
def delete_folder(request, folder_name):
    client_profile = ClientProfile.objects.get(user=request.user)
    if not client_profile.storage_path:
        messages.error(request, "Storage not configured.")
        return redirect("dashboard")

    # Decode folder name
    folder_name = unquote(folder_name)
    
    # Delete all DB entries under this folder
    ClientFile.objects.filter(
        client=client_profile,
        relative_path__startswith=folder_name + '/'
    ).delete()

    # Delete folder on disk
    folder_path = os.path.join(client_profile.storage_path, folder_name)
    if os.path.exists(folder_path):
        shutil.rmtree(folder_path)

    messages.success(request, f"Folder '{folder_name}' deleted.")
    return redirect("dashboard")