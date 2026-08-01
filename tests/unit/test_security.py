import uuid
from datetime import datetime, timedelta, timezone

import pytest
from jose import jwt

from nucleus_api.core.config import settings
from nucleus_api.core.security import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)


class TestHashPassword:
    def test_returns_bcrypt_hash(self):
        hashed = hash_password("mysecret")
        assert hashed.startswith("$2b$")

    def test_hash_differs_from_plaintext(self):
        assert hash_password("mysecret") != "mysecret"

    def test_same_password_produces_different_hashes(self):
        # bcrypt uses a random salt per call
        assert hash_password("mysecret") != hash_password("mysecret")


class TestVerifyPassword:
    def test_correct_password_returns_true(self):
        hashed = hash_password("correct")
        assert verify_password("correct", hashed) is True

    def test_wrong_password_returns_false(self):
        hashed = hash_password("correct")
        assert verify_password("wrong", hashed) is False

    def test_empty_password_returns_false(self):
        hashed = hash_password("notempty")
        assert verify_password("", hashed) is False


class TestCreateAccessToken:
    def test_returns_non_empty_string(self):
        token = create_access_token(uuid.uuid4())
        assert isinstance(token, str) and len(token) > 0

    def test_payload_contains_correct_subject(self):
        user_id = uuid.uuid4()
        token = create_access_token(user_id)
        payload = decode_access_token(token)
        assert payload["sub"] == str(user_id)

    def test_token_has_expiry(self):
        token = create_access_token(uuid.uuid4())
        payload = decode_access_token(token)
        assert "exp" in payload


class TestDecodeAccessToken:
    def test_decodes_valid_token(self):
        user_id = uuid.uuid4()
        payload = decode_access_token(create_access_token(user_id))
        assert payload["sub"] == str(user_id)

    def test_returns_none_for_random_string(self):
        assert decode_access_token("not.a.token") is None

    def test_returns_none_for_tampered_signature(self):
        token = create_access_token(uuid.uuid4())
        # flip the last few characters of the signature segment
        tampered = token[:-5] + "XXXXX"
        assert decode_access_token(tampered) is None

    def test_returns_none_for_expired_token(self):
        expired_payload = {
            "sub": str(uuid.uuid4()),
            "exp": datetime.now(timezone.utc) - timedelta(seconds=1),
        }
        expired_token = jwt.encode(
            expired_payload, settings.secret_key, algorithm=settings.algorithm
        )
        assert decode_access_token(expired_token) is None

    def test_returns_none_for_wrong_secret(self):
        payload = {"sub": str(uuid.uuid4()), "exp": datetime.now(timezone.utc) + timedelta(minutes=15)}
        token_wrong_secret = jwt.encode(payload, "wrong-secret", algorithm=settings.algorithm)
        assert decode_access_token(token_wrong_secret) is None


class TestCreateRefreshToken:
    def test_returns_non_empty_string(self):
        token = create_refresh_token()
        assert isinstance(token, str) and len(token) > 0

    def test_each_call_produces_unique_token(self):
        assert create_refresh_token() != create_refresh_token()


class TestHashRefreshToken:
    def test_is_deterministic(self):
        raw = "fixed-input"
        assert hash_refresh_token(raw) == hash_refresh_token(raw)

    def test_different_inputs_produce_different_hashes(self):
        assert hash_refresh_token("token-a") != hash_refresh_token("token-b")

    def test_output_is_64_char_hex(self):
        result = hash_refresh_token("anything")
        assert len(result) == 64
        int(result, 16)  # raises ValueError if not valid hex
