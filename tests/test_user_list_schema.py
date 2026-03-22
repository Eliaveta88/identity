"""UserListResponse schema (admin list) — контракт для плана P2."""

import unittest

from src.routers.v1.identity.schemas import UserListResponse, UserResponse


class TestUserListResponse(unittest.TestCase):
    def test_parse_typical_payload(self) -> None:
        data = {
            "items": [
                {
                    "id": 1,
                    "username": "admin",
                    "email": "a@example.com",
                    "roles": ["admin"],
                },
            ],
            "total": 1,
            "skip": 0,
            "limit": 50,
        }
        m = UserListResponse.model_validate(data)
        self.assertEqual(m.total, 1)
        self.assertEqual(len(m.items), 1)
        self.assertIsInstance(m.items[0], UserResponse)
        self.assertEqual(m.items[0].username, "admin")

    def test_empty_items(self) -> None:
        m = UserListResponse.model_validate({"items": [], "total": 0, "skip": 0, "limit": 100})
        self.assertEqual(m.total, 0)


if __name__ == "__main__":
    unittest.main()
