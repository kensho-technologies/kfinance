from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
import httpx2
import jwt
from respx import Router

from kfinance.integrations.proxy_mcp.auth import (
    Cache,
    ClientAccessToken,
    PrivateKeyBasedAccessTokenDispenser,
)


OKTA_HOST = "https://kensho.okta.com"
TOKEN_URL = f"{OKTA_HOST}/oauth2/default/v1/token"


def _private_key_pem() -> str:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    return key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()


class TestPrivateKeyDispenserKid:
    """The dispenser builds its own assertion, so it needs its own kid coverage."""

    def _captured_assertion(self, httpx2_mock: Router, kid: str | None) -> str:
        route = httpx2_mock.post(TOKEN_URL).respond(json={"access_token": "fake_token"})
        cache: Cache[ClientAccessToken] = Cache()
        dispenser = PrivateKeyBasedAccessTokenDispenser(
            client_id="testapp",
            private_key=_private_key_pem(),
            kid=kid,
            cache=cache,
            access_token_cache_key="test_token",
            okta_host=OKTA_HOST,
        )
        dispenser.refresh_access_token()
        return httpx2.QueryParams(route.calls.last.request.content.decode())["client_assertion"]

    def test_assertion_stamps_kid_header(self, httpx2_mock: Router) -> None:
        assertion = self._captured_assertion(httpx2_mock, kid="my-key-id")
        assert jwt.get_unverified_header(assertion)["kid"] == "my-key-id"

    def test_assertion_omits_kid_header_when_unset(self, httpx2_mock: Router) -> None:
        assertion = self._captured_assertion(httpx2_mock, kid=None)
        assert "kid" not in jwt.get_unverified_header(assertion)
