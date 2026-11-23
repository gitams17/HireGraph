"""
Accounts test suite.

Covers:
  - Registration (success, password mismatch, duplicate email)
  - Login / Logout (success, invalid credentials)
  - /me endpoint (authenticated get, unauthenticated 403, profile update)
"""

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()

REGISTER_URL = "/api/v1/auth/register/"
LOGIN_URL = "/api/v1/auth/login/"
LOGOUT_URL = "/api/v1/auth/logout/"
ME_URL = "/api/v1/auth/me/"


def create_user(**kwargs):
    defaults = {
        "email": "user@example.com",
        "password": "securepassword1",
        "first_name": "Test",
        "last_name": "User",
    }
    defaults.update(kwargs)
    return User.objects.create_user(**defaults)


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


class RegistrationTests(APITestCase):
    def test_register_returns_201_and_user_data(self):
        payload = {
            "email": "alice@example.com",
            "first_name": "Alice",
            "last_name": "Smith",
            "password": "securepassword1",
            "confirm_password": "securepassword1",
        }
        response = self.client.post(REGISTER_URL, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["email"], "alice@example.com")
        self.assertNotIn("password", response.data)

    def test_register_creates_user_in_db(self):
        payload = {
            "email": "Bob@Example.com",  # Test email normalisation
            "first_name": "Bob",
            "last_name": "Jones",
            "password": "securepassword1",
            "confirm_password": "securepassword1",
        }
        self.client.post(REGISTER_URL, payload, format="json")
        self.assertTrue(User.objects.filter(email="bob@example.com").exists())

    def test_register_password_mismatch_returns_400(self):
        payload = {
            "email": "charlie@example.com",
            "first_name": "Charlie",
            "last_name": "Brown",
            "password": "securepassword1",
            "confirm_password": "different_password",
        }
        response = self.client.post(REGISTER_URL, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_duplicate_email_returns_400(self):
        create_user(email="dave@example.com")
        payload = {
            "email": "dave@example.com",
            "first_name": "Dave",
            "last_name": "Miller",
            "password": "securepassword1",
            "confirm_password": "securepassword1",
        }
        response = self.client.post(REGISTER_URL, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_short_password_returns_400(self):
        payload = {
            "email": "eve@example.com",
            "first_name": "Eve",
            "last_name": "Adams",
            "password": "short",
            "confirm_password": "short",
        }
        response = self.client.post(REGISTER_URL, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# ---------------------------------------------------------------------------
# Login / Logout
# ---------------------------------------------------------------------------


class LoginTests(APITestCase):
    def setUp(self):
        self.user = create_user(email="frank@example.com", password="securepassword1")

    def test_login_valid_credentials_returns_200(self):
        response = self.client.post(
            LOGIN_URL,
            {"email": "frank@example.com", "password": "securepassword1"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], "frank@example.com")

    def test_login_wrong_password_returns_400(self):
        response = self.client.post(
            LOGIN_URL,
            {"email": "frank@example.com", "password": "wrongpassword"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_nonexistent_email_returns_400(self):
        response = self.client.post(
            LOGIN_URL,
            {"email": "nobody@example.com", "password": "securepassword1"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_logout_authenticated_returns_200(self):
        self.client.force_login(self.user)
        response = self.client.post(LOGOUT_URL, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_logout_unauthenticated_returns_403(self):
        response = self.client.post(LOGOUT_URL, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


# ---------------------------------------------------------------------------
# Me
# ---------------------------------------------------------------------------


class MeTests(APITestCase):
    def setUp(self):
        self.user = create_user(
            email="grace@example.com",
            first_name="Grace",
            last_name="Hopper",
        )

    def test_me_authenticated_returns_user_data(self):
        self.client.force_login(self.user)
        response = self.client.get(ME_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], "grace@example.com")
        self.assertEqual(response.data["full_name"], "Grace Hopper")

    def test_me_unauthenticated_returns_403(self):
        response = self.client.get(ME_URL)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_me_patch_updates_name(self):
        self.client.force_login(self.user)
        response = self.client.patch(
            ME_URL,
            {"first_name": "Ada", "last_name": "Lovelace"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["full_name"], "Ada Lovelace")
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Ada")
