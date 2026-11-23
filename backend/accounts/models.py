"""Custom user model using email as the primary identifier.

Defined here from day one to avoid expensive schema migrations later.
AbstractUser keeps Django's built-in groups, permissions, and admin intact;
we only swap the natural key from username → email.
"""

import uuid

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    """Manager that removes the username field requirement."""

    def create_user(self, email: str, password: str | None = None, **extra_fields):
        if not email:
            raise ValueError("An email address is required.")
        email = self.normalize_email(email)
        extra_fields.setdefault("is_active", True)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email: str, password: str | None = None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if not extra_fields.get("is_staff"):
            raise ValueError("Superuser must have is_staff=True.")
        if not extra_fields.get("is_superuser"):
            raise ValueError("Superuser must have is_superuser=True.")
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """Email-primary user; username field removed entirely."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # Remove the username field that AbstractUser inherits.
    username = None  # type: ignore[assignment]
    email = models.EmailField(unique=True, db_index=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)

    USERNAME_FIELD = "email"
    # first_name and last_name are required when calling createsuperuser.
    REQUIRED_FIELDS = ["first_name", "last_name"]

    objects = UserManager()  # type: ignore[assignment]

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
        ordering = ["-date_joined"]

    def __str__(self) -> str:
        return self.email

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()
