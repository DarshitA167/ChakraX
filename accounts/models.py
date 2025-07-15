from django.db import models
from django.conf import settings
from decouple import config
from cryptography.fernet import Fernet

# ✅ Load key from .env
SECRET_KEY = config("CHAKRAX_ENCRYPTION_KEY")
fernet = Fernet(SECRET_KEY)

def encrypt_password(raw_password: str) -> str:
    return fernet.encrypt(raw_password.encode()).decode()

def decrypt_password(encrypted_password: str) -> str:
    return fernet.decrypt(encrypted_password.encode()).decode()

class PasswordVault(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    site_name = models.CharField(max_length=255)
    site_url = models.URLField(blank=True, null=True)
    username_or_email = models.CharField(max_length=255)
    encrypted_password = models.TextField()

    def __str__(self):
        return f"{self.site_name} ({self.username_or_email})"

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from decouple import config
from cryptography.fernet import Fernet

# ✅ Custom User Model
class CustomUser(AbstractUser):
    # Add custom fields later if needed, e.g.:
    # role = models.CharField(max_length=50, default="user")
    pass

# ✅ Load Encryption Key
SECRET_KEY = config("CHAKRAX_ENCRYPTION_KEY")
fernet = Fernet(SECRET_KEY)

def encrypt_password(raw_password: str) -> str:
    return fernet.encrypt(raw_password.encode()).decode()

def decrypt_password(encrypted_password: str) -> str:
    return fernet.decrypt(encrypted_password.encode()).decode()

# ✅ Password Vault Model
class PasswordVault(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    site_name = models.CharField(max_length=255)
    site_url = models.URLField(blank=True, null=True)
    username_or_email = models.CharField(max_length=255)
    encrypted_password = models.TextField()

    def __str__(self):
        return f"{self.site_name} ({self.username_or_email})"

