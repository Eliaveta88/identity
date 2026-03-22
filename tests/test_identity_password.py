"""Unit tests for password hashing (bcrypt + legacy dev format)."""

from __future__ import annotations

import unittest

from src.routers.v1.identity.dal import UserDAL


class IdentityPasswordTests(unittest.TestCase):
    def test_bcrypt_hash_verify_roundtrip(self) -> None:
        raw = "SecretPass123!"
        hashed = UserDAL.hash_password(raw)
        self.assertTrue(hashed.startswith("$2"))
        self.assertTrue(UserDAL.verify_password(raw, hashed))
        self.assertFalse(UserDAL.verify_password("wrong", hashed))

    def test_legacy_hashed_plain_format(self) -> None:
        self.assertTrue(UserDAL.verify_password("demo", "hashed_demo"))
        self.assertFalse(UserDAL.verify_password("other", "hashed_demo"))
