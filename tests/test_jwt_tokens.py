"""Tests for JWT helpers."""

import unittest

from src.services.jwt_tokens import (
    TOKEN_TYPE_ACCESS,
    TOKEN_TYPE_REFRESH,
    create_access_token,
    create_refresh_token,
    decode_token,
    new_token_ids,
)


class JwtTokenTests(unittest.TestCase):
    def test_access_refresh_roundtrip(self) -> None:
        session_id, access_jti, refresh_jti = new_token_ids()
        access = create_access_token(42, access_jti, session_id)
        refresh = create_refresh_token(42, refresh_jti, session_id)

        a = decode_token(access)
        r = decode_token(refresh)

        self.assertEqual(a["typ"], TOKEN_TYPE_ACCESS)
        self.assertEqual(r["typ"], TOKEN_TYPE_REFRESH)
        self.assertEqual(a["sub"], "42")
        self.assertEqual(r["sub"], "42")
        self.assertEqual(a["sid"], session_id)
        self.assertEqual(r["sid"], session_id)
        self.assertEqual(a["jti"], access_jti)
        self.assertEqual(r["jti"], refresh_jti)
