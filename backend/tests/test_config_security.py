import os
import unittest
from unittest.mock import patch

from pydantic import ValidationError

from app.config import Settings


class SettingsSecurityTests(unittest.TestCase):
    def test_positive_access_token_expiry_is_accepted(self):
        settings = Settings(
            _env_file=None,
            AUTH_ACCESS_TOKEN_EXPIRE_MINUTES=60,
        )
        self.assertEqual(settings.AUTH_ACCESS_TOKEN_EXPIRE_MINUTES, 60)

    def test_zero_access_token_expiry_is_rejected(self):
        with self.assertRaisesRegex(
            ValidationError,
            "AUTH_ACCESS_TOKEN_EXPIRE_MINUTES must be greater than zero",
        ):
            Settings(
                _env_file=None,
                AUTH_ACCESS_TOKEN_EXPIRE_MINUTES=0,
            )

    def test_negative_access_token_expiry_is_rejected(self):
        with self.assertRaisesRegex(
            ValidationError,
            "AUTH_ACCESS_TOKEN_EXPIRE_MINUTES must be greater than zero",
        ):
            Settings(
                _env_file=None,
                AUTH_ACCESS_TOKEN_EXPIRE_MINUTES=-15,
            )

    def test_zero_access_token_expiry_from_environment_is_rejected(self):
        with patch.dict(
            os.environ,
            {"AUTH_ACCESS_TOKEN_EXPIRE_MINUTES": "0"},
            clear=True,
        ):
            with self.assertRaisesRegex(
                ValidationError,
                "AUTH_ACCESS_TOKEN_EXPIRE_MINUTES must be greater than zero",
            ):
                Settings(_env_file=None)

    def test_negative_access_token_expiry_from_environment_is_rejected(self):
        with patch.dict(
            os.environ,
            {"AUTH_ACCESS_TOKEN_EXPIRE_MINUTES": "-15"},
            clear=True,
        ):
            with self.assertRaisesRegex(
                ValidationError,
                "AUTH_ACCESS_TOKEN_EXPIRE_MINUTES must be greater than zero",
            ):
                Settings(_env_file=None)

    def test_valid_production_secret_is_accepted(self):
        settings = Settings(
            _env_file=None,
            APP_ENV="production",
            AUTH_SECRET_KEY="A" * 32,
        )
        self.assertEqual(settings.AUTH_SECRET_KEY, "A" * 32)

    def test_short_production_secret_is_rejected(self):
        with self.assertRaisesRegex(
            ValidationError,
            "AUTH_SECRET_KEY must be a secure production secret",
        ):
            Settings(
                _env_file=None,
                APP_ENV="production",
                AUTH_SECRET_KEY="short",
            )

    def test_development_fallback_secret_is_rejected_in_production(self):
        with self.assertRaisesRegex(
            ValidationError,
            "AUTH_SECRET_KEY must be a secure production secret",
        ):
            Settings(
                _env_file=None,
                APP_ENV="production",
                AUTH_SECRET_KEY="change-this-development-secret-key",
            )

    def test_replace_with_placeholder_is_rejected_in_production(self):
        with self.assertRaisesRegex(
            ValidationError,
            "AUTH_SECRET_KEY must be a secure production secret",
        ):
            Settings(
                _env_file=None,
                APP_ENV="production",
                AUTH_SECRET_KEY="replace-with-a-long-random-secret",
            )

    def test_placeholder_case_variants_are_rejected_in_production(self):
        with self.assertRaisesRegex(
            ValidationError,
            "AUTH_SECRET_KEY must be a secure production secret",
        ):
            Settings(
                _env_file=None,
                APP_ENV="production",
                AUTH_SECRET_KEY="Replace-With-a-long-random-secret",
            )

    def test_placeholder_secret_with_leading_whitespace_is_rejected(self):
        with self.assertRaisesRegex(
            ValidationError,
            "AUTH_SECRET_KEY must be a secure production secret",
        ):
            Settings(
                _env_file=None,
                APP_ENV="production",
                AUTH_SECRET_KEY="  replace-with-a-long-random-secret",
            )

    def test_placeholder_secret_with_trailing_whitespace_is_rejected(self):
        with self.assertRaisesRegex(
            ValidationError,
            "AUTH_SECRET_KEY must be a secure production secret",
        ):
            Settings(
                _env_file=None,
                APP_ENV="production",
                AUTH_SECRET_KEY="replace-with-a-long-random-secret  ",
            )

    def test_placeholder_secret_is_allowed_outside_production(self):
        settings = Settings(
            _env_file=None,
            APP_ENV="development",
            AUTH_SECRET_KEY="replace-with-a-long-random-secret",
        )
        self.assertEqual(
            settings.AUTH_SECRET_KEY,
            "replace-with-a-long-random-secret",
        )


if __name__ == "__main__":
    unittest.main()
