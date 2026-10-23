from types import SimpleNamespace
from unittest import IsolatedAsyncioTestCase, TestCase
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from tests.support import build_test_app


class AuthServiceTests(IsolatedAsyncioTestCase):
    async def test_validate_password_reports_each_requirement(self):
        from app.services.auth_services import validate_password

        result = validate_password("GoodPass1!")

        self.assertTrue(result["is_valid"])
        self.assertTrue(all(check["passed"] for check in result["results"].values()))

        invalid = validate_password("weak")
        self.assertFalse(invalid["is_valid"])
        self.assertEqual(
            {
                name
                for name, check in invalid["results"].items()
                if not check["passed"]
            },
            {
                "min_length_8",
                "has_uppercase",
                "has_number",
                "has_special_char",
            },
        )

    async def test_add_admin_user_creates_admin_and_commits(self):
        from app.core.security import hasher
        from app.models.enums import UserRole
        from app.schemas.auth_schemas import AddAdmin
        from app.services.auth_services import add_admin_user

        db = AsyncMock()
        db.add = MagicMock()
        with (
            patch("app.services.auth_services.get_user", new=AsyncMock(return_value=None)),
            patch.object(hasher, "hash", return_value="hashed-password"),
        ):
            response = await add_admin_user(
                AddAdmin(email="admin@example.com", password="GoodPass1!"),
                UserRole.admin,
                db,
            )

        self.assertEqual(response.email, "admin@example.com")
        self.assertEqual(response.message, "User created successfully")
        created_user = db.add.call_args.args[0]
        self.assertEqual(created_user.email, "admin@example.com")
        self.assertEqual(created_user.password_hash, "hashed-password")
        self.assertEqual(created_user.role, UserRole.admin)
        db.commit.assert_awaited_once()
        db.refresh.assert_awaited_once_with(created_user)

    async def test_add_admin_user_rejects_duplicate_email(self):
        from app.core.exceptions import EmailAlreadyRegisteredException
        from app.models.enums import UserRole
        from app.schemas.auth_schemas import AddAdmin
        from app.services.auth_services import add_admin_user

        db = AsyncMock()
        db.add = MagicMock()
        with patch(
            "app.services.auth_services.get_user",
            new=AsyncMock(return_value=object()),
        ):
            with self.assertRaises(EmailAlreadyRegisteredException):
                await add_admin_user(
                    AddAdmin(email="admin@example.com", password="GoodPass1!"),
                    UserRole.admin,
                    db,
                )

        db.commit.assert_not_awaited()

    async def test_add_admin_user_rolls_back_on_unique_constraint_error(self):
        from sqlalchemy.exc import IntegrityError

        from app.core.exceptions import UserAlreadyRegisteredException
        from app.models.enums import UserRole
        from app.schemas.auth_schemas import AddAdmin
        from app.services.auth_services import add_admin_user

        db = AsyncMock()
        db.add = MagicMock()
        db.commit.side_effect = IntegrityError("insert", {}, Exception("duplicate"))
        with (
            patch("app.services.auth_services.get_user", new=AsyncMock(return_value=None)),
            patch("app.services.auth_services.hasher.hash", return_value="hashed"),
        ):
            with self.assertRaises(UserAlreadyRegisteredException):
                await add_admin_user(
                    AddAdmin(email="admin@example.com", password="GoodPass1!"),
                    UserRole.admin,
                    db,
                )

        db.rollback.assert_awaited_once()

    async def test_register_user_rejects_a_weak_password(self):
        from app.core.exceptions import PasswordRequirementsNotMetException
        from app.schemas.auth_schemas import RegisterRequest
        from app.services.auth_services import create_new_user

        with self.assertRaises(PasswordRequirementsNotMetException):
            await create_new_user(
                RegisterRequest(
                    invite_code="invite-code",
                    email="client@example.com",
                    password="weak",
                ),
                AsyncMock(),
            )


class AuthRouteIntegrationTests(TestCase):
    def setUp(self):
        from app.api.v1 import auth
        from app.core.security import get_current_user, get_db

        self.app = build_test_app()
        self.app.dependency_overrides[get_db] = lambda: AsyncMock()
        self.app.dependency_overrides[get_current_user] = lambda: {
            "id": "user-id",
            "email": "client@example.com",
        }
        self.client = TestClient(self.app)
        self.auth_routes = auth

    def tearDown(self):
        self.app.dependency_overrides.clear()

    def test_login_returns_bearer_token_for_valid_credentials(self):
        with (
            patch.object(
                self.auth_routes,
                "authenticate_user",
                new=AsyncMock(
                    return_value=SimpleNamespace(email_address="admin@example.com")
                ),
            ),
            patch.object(
                self.auth_routes, "create_access_token", return_value="signed-token"
            ),
        ):
            response = self.client.post(
                "/api/v1/auth/login",
                data={"username": "admin@example.com", "password": "GoodPass1!"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "access_token": "signed-token",
                "token_type": "bearer",
                "refresh_token": "sample_refresh_token",
            },
        )

    def test_login_rejects_invalid_credentials(self):
        with patch.object(
            self.auth_routes,
            "authenticate_user",
            new=AsyncMock(return_value=False),
        ):
            response = self.client.post(
                "/api/v1/auth/login",
                data={"username": "admin@example.com", "password": "wrong"},
            )

        self.assertEqual(response.status_code, 401)

    def test_current_user_returns_authenticated_user(self):
        response = self.client.get("/api/v1/auth/me")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"id": "user-id", "email": "client@example.com"},
        )

    def test_register_route_passes_registration_to_service(self):
        from app.schemas.auth_schemas import RegisterRequestResponse

        result = RegisterRequestResponse(
            id="user-id",
            email="client@example.com",
            role="client",
            client_id="client-id",
            is_active=True,
            created_at="2025-01-01T00:00:00Z",
        )
        with patch.object(
            self.auth_routes,
            "create_new_user",
            new=AsyncMock(return_value=result),
        ) as create_user:
            response = self.client.post(
                "/api/v1/auth/register",
                json={
                    "invite_code": "invite-code",
                    "email": "client@example.com",
                    "password": "GoodPass1!",
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["email"], "client@example.com")
        create_user.assert_awaited_once()
        self.assertEqual(create_user.await_args.args[0].invite_code, "invite-code")


if __name__ == "__main__":
    import unittest

    unittest.main()