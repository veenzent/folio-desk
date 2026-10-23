from types import SimpleNamespace
from unittest import IsolatedAsyncioTestCase, TestCase
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from tests.support import build_test_app, client_response


class ClientServiceTests(IsolatedAsyncioTestCase):
    async def test_create_client_adds_and_commits_new_client(self):
        from app.models.enums import ClientTier
        from app.schemas.client_schemas import AddClient
        from app.services.client_services import create_new_client

        db = AsyncMock()
        db.add = MagicMock()
        with patch(
            "app.services.client_services.get_client",
            new=AsyncMock(return_value=None),
        ):
            response = await create_new_client(
                AddClient(name="Example Client", contact_email="client@example.com"),
                ClientTier.premium,
                db,
            )

        self.assertEqual(response.name, "Example Client")
        self.assertEqual(response.contact_email, "client@example.com")
        self.assertEqual(response.tier, ClientTier.premium)
        created_client = db.add.call_args.args[0]
        db.commit.assert_awaited_once()
        db.refresh.assert_awaited_once_with(created_client)

    async def test_create_client_rejects_an_existing_contact_email(self):
        from app.core.exceptions import EmailAlreadyRegisteredException
        from app.models.enums import ClientTier
        from app.schemas.client_schemas import AddClient
        from app.services.client_services import create_new_client

        db = AsyncMock()
        db.add = MagicMock()
        with patch(
            "app.services.client_services.get_client",
            new=AsyncMock(return_value=object()),
        ):
            with self.assertRaises(EmailAlreadyRegisteredException):
                await create_new_client(
                    AddClient(name="Example Client", contact_email="client@example.com"),
                    ClientTier.standard,
                    db,
                )

        db.commit.assert_not_awaited()

    async def test_get_client_maps_a_database_record(self):
        from app.services.client_services import get_client

        record = client_response()
        result = SimpleNamespace(
            scalar_one_or_none=MagicMock(return_value=SimpleNamespace(**record))
        )
        db = AsyncMock()
        db.execute.return_value = result

        response = await get_client(db, "client@example.com")

        self.assertEqual(response.id, record["id"])
        self.assertEqual(response.contact_email, record["contact_email"])

    async def test_get_client_returns_none_when_not_found(self):
        from app.services.client_services import get_client

        db = AsyncMock()
        db.execute.return_value = SimpleNamespace(
            scalar_one_or_none=MagicMock(return_value=None)
        )

        self.assertIsNone(await get_client(db, "missing@example.com"))

    async def test_get_all_clients_applies_pagination(self):
        from app.services.client_services import get_all_clients

        record = SimpleNamespace(**client_response())
        scalars = SimpleNamespace(all=MagicMock(return_value=[record]))
        db = AsyncMock()
        db.execute.return_value = SimpleNamespace(scalars=MagicMock(return_value=scalars))

        response = await get_all_clients(db, skip=5, limit=3)

        self.assertEqual(len(response), 1)
        self.assertEqual(response[0].id, record.id)
        statement = db.execute.await_args.args[0]
        self.assertEqual(statement._offset, 5)
        self.assertEqual(statement._limit, 3)

    async def test_delete_client_commits_when_record_exists(self):
        from app.services.client_services import delete_client

        db = AsyncMock()
        db.execute.return_value = SimpleNamespace(rowcount=1)

        await delete_client("client-id", db)

        db.commit.assert_awaited_once()

    async def test_delete_client_returns_not_found_for_missing_record(self):
        from fastapi import HTTPException

        from app.services.client_services import delete_client

        db = AsyncMock()
        db.execute.return_value = SimpleNamespace(rowcount=0)

        with self.assertRaises(HTTPException) as raised:
            await delete_client("missing-id", db)

        self.assertEqual(raised.exception.status_code, 404)
        db.commit.assert_not_awaited()


class ClientRouteIntegrationTests(TestCase):
    def setUp(self):
        from app.api.v1 import client
        from app.core.security import get_current_admin, get_db

        self.app = build_test_app()
        self.app.dependency_overrides[get_db] = lambda: AsyncMock()
        self.app.dependency_overrides[get_current_admin] = lambda: {"role": "admin"}
        self.client = TestClient(self.app)
        self.client_routes = client

    def tearDown(self):
        self.app.dependency_overrides.clear()

    def test_create_client_route_returns_created_client(self):
        result = client_response()
        with patch.object(
            self.client_routes,
            "create_new_client",
            new=AsyncMock(return_value=result),
        ) as create_client:
            response = self.client.post(
                "/api/v1/clients?tier=standard",
                json={
                    "name": "Example Client",
                    "contact_email": "client@example.com",
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["contact_email"], "client@example.com")
        self.assertEqual(create_client.await_args.args[1].value, "standard")

    def test_get_clients_route_converts_page_to_offset_and_limit(self):
        result = [client_response()]
        with patch.object(
            self.client_routes,
            "get_all_clients",
            new=AsyncMock(return_value=result),
        ) as get_clients:
            response = self.client.get("/api/v1/clients?page_size=4&page_number=3")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(get_clients.await_args.kwargs, {"skip": 8, "limit": 4})

    def test_delete_client_route_returns_confirmation(self):
        with patch.object(
            self.client_routes,
            "delete_client",
            new=AsyncMock(return_value=None),
        ) as delete_client:
            response = self.client.delete("/api/v1/clients/client-id")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"message": "Client with ID client-id has been deleted."},
        )
        delete_client.assert_awaited_once()
        self.assertEqual(delete_client.await_args.args[0], "client-id")
        self.assertIsInstance(delete_client.await_args.args[1], AsyncMock)

    def test_client_routes_require_admin_dependency(self):
        from app.core.exceptions import InvalidRoleException
        from app.core.security import get_current_admin

        async def reject_admin():
            raise InvalidRoleException()

        self.app.dependency_overrides[get_current_admin] = reject_admin

        response = self.client.get("/api/v1/clients")

        self.assertEqual(response.status_code, 403)


if __name__ == "__main__":
    import unittest

    unittest.main()
