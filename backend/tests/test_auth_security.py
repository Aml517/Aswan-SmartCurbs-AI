import base64
import hashlib
import hmac
import json
import unittest

from fastapi import HTTPException

from app.config import settings
from app.services.auth_service import (
    PBKDF2_ITERATIONS,
    _base64url_encode,
    decode_access_token,
    verify_password,
    hash_password,
)


class PasswordHashValidationTests(unittest.TestCase):
    def test_current_application_hash_is_accepted(self):
        password_hash = hash_password("correct-password")
        self.assertTrue(verify_password("correct-password", password_hash))
        self.assertFalse(verify_password("wrong-password", password_hash))

    def test_supported_algorithm_is_required(self):
        valid_hash = hash_password("password")
        unsupported = "pbkdf2_sha512$600000$" + "$".join(valid_hash.split("$")[2:])
        self.assertFalse(verify_password("password", unsupported))

    def test_exact_hash_part_count_is_required(self):
        for malformed in (
            "",
            "pbkdf2_sha256$600000$salt",
            "pbkdf2_sha256$600000$salt$digest$extra",
        ):
            with self.subTest(malformed=malformed):
                self.assertFalse(verify_password("password", malformed))

    def test_salt_format_and_length_are_validated(self):
        valid_hash = hash_password("password")
        _, iterations, _, digest = valid_hash.split("$", 3)
        for salt in ("", "0" * 31, "g" * 32, "0" * 32 + "00"):
            with self.subTest(salt=salt):
                malformed = f"pbkdf2_sha256${iterations}${salt}${digest}"
                self.assertFalse(verify_password("password", malformed))

    def test_digest_format_and_length_are_validated(self):
        valid_hash = hash_password("password")
        _, iterations, salt, _ = valid_hash.split("$", 3)
        for digest in ("", "A" * 42, "A" * 44, "A" * 42 + "+"):
            with self.subTest(digest=digest):
                malformed = f"pbkdf2_sha256${iterations}${salt}${digest}"
                self.assertFalse(verify_password("password", malformed))

    def test_unsupported_iteration_count_is_rejected(self):
        valid_hash = hash_password("password")
        _, _, salt, digest = valid_hash.split("$", 3)
        for iterations in (0, 1, PBKDF2_ITERATIONS + 1, PBKDF2_ITERATIONS - 1):
            with self.subTest(iterations=iterations):
                malformed = f"pbkdf2_sha256${iterations}${salt}${digest}"
                self.assertFalse(verify_password("password", malformed))

    def test_noncanonical_supported_iteration_text_is_rejected(self):
        valid_hash = hash_password("password")
        _, _, salt, digest = valid_hash.split("$", 3)
        for iteration_text in ("+600000", "0600000", " 600000", "600000 ", "600000\n"):
            with self.subTest(iteration_text=iteration_text):
                malformed = f"pbkdf2_sha256${iteration_text}${salt}${digest}"
                self.assertFalse(verify_password("password", malformed))


class JWTValidationTests(unittest.TestCase):
    def setUp(self):
        self.original_secret = settings.AUTH_SECRET_KEY
        self.original_algorithm = settings.AUTH_ALGORITHM
        settings.AUTH_SECRET_KEY = "unit-test-secret-at-least-32-characters-long"
        settings.AUTH_ALGORITHM = "HS256"

    def tearDown(self):
        settings.AUTH_SECRET_KEY = self.original_secret
        settings.AUTH_ALGORITHM = self.original_algorithm

    def encode_segment(self, value):
        return _base64url_encode(
            json.dumps(value, separators=(",", ":")).encode("utf-8")
        )

    def encode_token(self, header=None, payload=None, signature=None):
        if header is None:
            header = {"alg": "HS256", "typ": "JWT"}
        if payload is None:
            now = int(__import__("time").time())
            payload = {"sub": "123", "role": "driver", "iat": now - 10, "exp": now + 60}
        header_segment = self.encode_segment(header)
        payload_segment = self.encode_segment(payload)
        signing_input = f"{header_segment}.{payload_segment}".encode("ascii")
        if signature is None:
            signature_bytes = hmac.new(
                settings.AUTH_SECRET_KEY.encode("utf-8"),
                signing_input,
                hashlib.sha256,
            ).digest()
        else:
            signature_bytes = signature
        return f"{header_segment}.{payload_segment}.{_base64url_encode(signature_bytes)}"

    def assert_invalid(self, token):
        with self.assertRaises(HTTPException) as context:
            decode_access_token(token)
        self.assertEqual(context.exception.status_code, 401)

    def test_valid_token_is_accepted(self):
        token = self.encode_token()
        payload = decode_access_token(token)
        self.assertEqual(payload["sub"], 123)
        self.assertEqual(payload["role"], "driver")

    def test_exp_boolean_is_rejected(self):
        now = int(__import__("time").time())
        self.assert_invalid(
            self.encode_token(payload={"sub": "123", "role": "driver", "iat": now - 10, "exp": True})
        )

    def test_exp_string_is_rejected(self):
        now = int(__import__("time").time())
        self.assert_invalid(
            self.encode_token(payload={"sub": "123", "role": "driver", "iat": now - 10, "exp": str(now + 60)})
        )

    def test_sub_must_be_canonical_positive_integer_string(self):
        now = int(__import__("time").time())
        for user_id in (123, "0", "-1", "+123", "0123", "", " 123"):
            with self.subTest(user_id=user_id):
                self.assert_invalid(
                    self.encode_token(
                        payload={"sub": user_id, "role": "driver", "iat": now - 10, "exp": now + 60}
                    )
                )

    def test_supported_roles_are_required(self):
        now = int(__import__("time").time())
        for role in ("owner", "Admin", "", None, 1):
            with self.subTest(role=role):
                self.assert_invalid(
                    self.encode_token(
                        payload={"sub": "123", "role": role, "iat": now - 10, "exp": now + 60}
                    )
                )

    def test_iat_must_be_integer(self):
        now = int(__import__("time").time())
        for issued_at in ("now", True, None, 1.5):
            with self.subTest(iat=issued_at):
                self.assert_invalid(
                    self.encode_token(
                        payload={"sub": "123", "role": "driver", "iat": issued_at, "exp": now + 60}
                    )
                )

    def test_future_iat_is_rejected(self):
        now = int(__import__("time").time())
        self.assert_invalid(
            self.encode_token(
                payload={"sub": "123", "role": "driver", "iat": now + 3600, "exp": now + 7200}
            )
        )

    def test_expiration_must_be_after_issuance(self):
        now = int(__import__("time").time())
        for expiration in (now - 20, now - 10):
            with self.subTest(expiration=expiration):
                self.assert_invalid(
                    self.encode_token(
                        payload={"sub": "123", "role": "driver", "iat": now - 10, "exp": expiration}
                    )
                )

    def test_expired_token_is_rejected(self):
        now = int(__import__("time").time())
        self.assert_invalid(
            self.encode_token(
                payload={"sub": "123", "role": "driver", "iat": now - 120, "exp": now - 60}
            )
        )

    def test_malformed_json_is_rejected(self):
        for segment in (b"not-json", b"[1,2,3]", b'"string"', b"null"):
            header_segment = _base64url_encode(segment)
            payload_segment = self.encode_segment(
                {"sub": "123", "role": "driver", "iat": 1, "exp": 4100000000}
            )
            signing_input = f"{header_segment}.{payload_segment}".encode("ascii")
            signature = hmac.new(
                settings.AUTH_SECRET_KEY.encode("utf-8"),
                signing_input,
                hashlib.sha256,
            ).digest()
            with self.subTest(segment=segment):
                self.assert_invalid(
                    f"{header_segment}.{payload_segment}.{_base64url_encode(signature)}"
                )

    def test_payload_json_must_be_an_object(self):
        for payload in ([], "string", None, 42):
            encoded = _base64url_encode(json.dumps(payload).encode("utf-8"))
            header_segment = self.encode_segment({"alg": "HS256", "typ": "JWT"})
            signing_input = f"{header_segment}.{encoded}".encode("ascii")
            signature = hmac.new(
                settings.AUTH_SECRET_KEY.encode("utf-8"),
                signing_input,
                hashlib.sha256,
            ).digest()
            with self.subTest(payload=payload):
                self.assert_invalid(
                    f"{header_segment}.{encoded}.{_base64url_encode(signature)}"
                )

    def test_invalid_payload_json_syntax_is_rejected(self):
        header_segment = self.encode_segment({"alg": "HS256", "typ": "JWT"})
        payload_segment = _base64url_encode(b'{"sub":"123","role":"driver"')
        signing_input = f"{header_segment}.{payload_segment}".encode("ascii")
        signature = hmac.new(
            settings.AUTH_SECRET_KEY.encode("utf-8"),
            signing_input,
            hashlib.sha256,
        ).digest()
        token = f"{header_segment}.{payload_segment}.{_base64url_encode(signature)}"
        self.assert_invalid(token)

    def test_invalid_base64url_characters_are_rejected(self):
        now = int(__import__("time").time())
        valid = self.encode_token(
            payload={"sub": "123", "role": "driver", "iat": now - 10, "exp": now + 60}
        )
        for invalid in (
            "abc*.def.ghi",
            "abc+.def.ghi",
            "abc=.def.ghi",
            valid.replace(".", "*", 1),
            "...",
            "a.b.c.d",
        ):
            with self.subTest(invalid=invalid):
                self.assert_invalid(invalid)

    def test_malformed_segment_lengths_are_rejected(self):
        self.assert_invalid("a.b.c")
        self.assert_invalid("ab.cd")

    def test_tampered_signature_is_rejected(self):
        token = self.encode_token()
        segments = token.split(".")
        segments[2] = ("A" if segments[2][0] != "A" else "B") + segments[2][1:]
        self.assert_invalid(".".join(segments))

    def test_wrong_algorithm_is_rejected(self):
        self.assert_invalid(
            self.encode_token(header={"alg": "HS512", "typ": "JWT"})
        )

    def test_missing_typ_is_rejected(self):
        self.assert_invalid(
            self.encode_token(header={"alg": "HS256"})
        )


if __name__ == "__main__":
    unittest.main()
