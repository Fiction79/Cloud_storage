# clients/models.py
import os
from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings


class ClientProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    storage_path = models.CharField(max_length=255, unique=True)
    quota_limit = models.BigIntegerField(
        null=True, blank=True,
        help_text="Storage quota in bytes. Example: 5*1024*1024*1024 for 5GB"
    )

    def __str__(self):
        return self.user.username

    def used_bytes(self):
        total = 0
        if os.path.exists(self.storage_path):
            for root, dirs, files in os.walk(self.storage_path):
                for f in files:
                    total += os.path.getsize(os.path.join(root, f))
        return total

    def used_human(self):
        return f"{self.used_bytes() / (1024**3):.2f} GB"

    def is_over_quota(self):
        if self.quota_limit is None:
            return False
        return self.used_bytes() > self.quota_limit


class ClientFile(models.Model):
    client = models.ForeignKey("ClientProfile", on_delete=models.CASCADE, related_name="files")
    name = models.CharField(max_length=255)          # e.g., "logo.png"
    relative_path = models.CharField(max_length=512, blank=True)  # e.g., "project/design/logo.png"
    size = models.FloatField()  # in MB
    uploaded_at = models.DateTimeField(auto_now_add=True)

    @property
    def extension(self):
        return os.path.splitext(self.name)[1].lower()

    @property
    def is_image(self):
        return self.extension in [".png", ".jpg", ".jpeg", ".gif", ".webp"]

    @property
    def is_video(self):
        return self.extension in [".mp4", ".mov", ".webm", ".ogg", ".avi", ".mkv"]

    @property
    def is_audio(self):
        return self.extension in [".mp3", ".wav", ".ogg", ".m4a", ".flac"]

    @property
    def is_pdf(self):
        return self.extension == ".pdf"

    @property
    def folder_name(self):
        if '/' in self.relative_path:
            return self.relative_path.split('/')[0]
        return None

    def __str__(self):
        return self.relative_path or self.name


@receiver(post_save, sender=User)
def create_client_profile(sender, instance, created, **kwargs):
    if created:
        if not hasattr(instance, 'clientprofile'):
            user_folder = os.path.join(settings.USER_DATA_ROOT, instance.username)
            os.makedirs(user_folder, exist_ok=True)
            ClientProfile.objects.create(
                user=instance,
                storage_path=user_folder,
                quota_limit=5 * 1024**3  # 5 GB
            )