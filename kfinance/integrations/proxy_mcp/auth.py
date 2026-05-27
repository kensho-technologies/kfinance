from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
import logging
import time
from typing import Generator, Generic, TypeVar

import httpx
from jwt import decode as jwt_decode, encode


T = TypeVar("T")

logger = logging.getLogger(__name__)


class CacheMissError(Exception):
    """Raised when a key is not found or has expired in the cache."""


class Cache(Generic[T]):
    """Simple in-memory key-value cache with optional TTL."""

    def __init__(self) -> None:
        """Initialize an empty cache."""
        self._items: dict[str, tuple[datetime | None, T]] = {}

    def get(self, key: str) -> T:
        """Return the cached value for key, or raise CacheMissError if missing/expired."""
        if key not in self._items:
            raise CacheMissError(key)
        expiration, value = self._items[key]
        if expiration is not None and datetime.now(tz=timezone.utc) > expiration:
            raise CacheMissError(key)
        return value

    def set(self, key: str, value: T, ttl: timedelta | None = None) -> None:
        """Store a value with an optional time-to-live."""
        expiration = datetime.now(tz=timezone.utc) + ttl if ttl is not None else None
        self._items[key] = (expiration, value)


class ClientAccessToken:
    """Wrapper around a raw JWT access token string with expiry helpers."""

    def __init__(self, token: str) -> None:
        """Initialize with a raw JWT string."""
        self.token = token

    def has_expired(self, buffer: timedelta = timedelta(seconds=0)) -> bool:
        """Return True if the token expires within the given buffer window."""
        return (self.ttl - buffer).total_seconds() <= 0

    @property
    def ttl(self) -> timedelta:
        """Return the remaining time-to-live based on the JWT exp claim."""
        # nosemgrep: python.jwt.security.unverified-jwt-decode.unverified-jwt-decode
        exp = jwt_decode(self.token, options={"verify_signature": False})["exp"]
        return timedelta(seconds=(exp - time.time()))


class ClientAccessTokenDispenser(ABC):
    """Base class for dispensers that acquire and cache access tokens."""

    TOKEN_CACHE_KEY_VERSION: int = 1
    _KEY_TEMPLATE: str = "{base}_v{version}"

    def __init__(
        self,
        cache: Cache[ClientAccessToken],
        access_token_cache_key: str,
        token_refresh_buffer: timedelta | None = None,
    ) -> None:
        """Initialize with a cache, cache key, and optional refresh buffer (default 1 min)."""
        if token_refresh_buffer is None:
            token_refresh_buffer = timedelta(minutes=1)
        self._cache = cache
        self._access_token_cache_key = self._KEY_TEMPLATE.format(
            base=access_token_cache_key,
            version=self.TOKEN_CACHE_KEY_VERSION,
        )
        self._token_refresh_buffer = token_refresh_buffer

    @property
    def access_token(self) -> ClientAccessToken:
        """Return a valid access token, refreshing if expired or near expiry."""
        try:
            token: ClientAccessToken | None = self._cache.get(self._access_token_cache_key)
        except CacheMissError:
            token = None

        if token is None or token.has_expired(self._token_refresh_buffer):
            token = self._refresh_and_cache()
        return token

    def _refresh_and_cache(self) -> ClientAccessToken:
        token = self.refresh_access_token()
        self._cache.set(
            key=self._access_token_cache_key,
            value=token,
            ttl=token.ttl - self._token_refresh_buffer,
        )
        return token

    @abstractmethod
    def refresh_access_token(self) -> ClientAccessToken:
        """Acquire a fresh access token. Implemented by subclasses."""


class RefreshTokenDispenser(ClientAccessTokenDispenser):
    """Exchanges a refresh token via GET {url}?refresh_token={token} -> {"access_token": "..."}."""

    def __init__(
        self,
        refresh_token: str,
        refresh_url: str,
        cache: Cache[ClientAccessToken],
        access_token_cache_key: str,
    ) -> None:
        """Initialize with a refresh token and the URL to exchange it at."""
        super().__init__(cache=cache, access_token_cache_key=access_token_cache_key)
        self._refresh_token = refresh_token
        self._refresh_url = refresh_url
        self._http_client = httpx.Client(timeout=60)

    def refresh_access_token(self) -> ClientAccessToken:
        """Exchange the refresh token for a new access token via HTTP GET."""
        response = self._http_client.get(
            f"{self._refresh_url}?refresh_token={self._refresh_token}",
        )
        response.raise_for_status()
        token = response.json()["access_token"]
        logger.info("Token acquired via refresh token exchange")
        return ClientAccessToken(token=token)


class PrivateKeyBasedAccessTokenDispenser(ClientAccessTokenDispenser):
    """An AccessTokenDispenser, which uses a private key to fetch access tokens."""

    def __init__(
        self,
        client_id: str,
        private_key: str,
        cache: Cache[ClientAccessToken],
        access_token_cache_key: str,
        okta_host: str,
        token_refresh_buffer: timedelta | None = None,
    ) -> None:
        """Initialize with client credentials and Okta host for JWT-based auth."""
        super().__init__(
            cache=cache,
            access_token_cache_key=access_token_cache_key,
            token_refresh_buffer=token_refresh_buffer,
        )

        self._client_id = client_id
        self._private_key = private_key
        self._okta_host = okta_host

    def refresh_access_token(self) -> ClientAccessToken:
        """Acquire a fresh access token via client_credentials grant with a signed JWT assertion."""
        iat = int(time.time())
        encoded = encode(
            {
                "aud": f"{self._okta_host}/oauth2/default/v1/token",
                "exp": iat + (60 * 60),
                "iat": iat,
                "sub": self._client_id,
                "iss": self._client_id,
            },
            self._private_key,
            algorithm="RS256",
        )
        response = httpx.post(
            f"{self._okta_host}/oauth2/default/v1/token",
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json",
            },
            data={
                "scope": "kensho:app:kfinance",
                "grant_type": "client_credentials",
                "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
                "client_assertion": encoded,
            },
            timeout=60,
        )
        response.raise_for_status()
        token_str = response.json().get("access_token")
        return ClientAccessToken(token=token_str)


class DynamicBearerAuth(httpx.Auth):
    """httpx Auth that injects a fresh Bearer token from a dispenser on every request."""

    def __init__(self, dispenser: ClientAccessTokenDispenser) -> None:
        """Initialize with a token dispenser."""
        self._dispenser = dispenser

    def auth_flow(self, request: httpx.Request) -> Generator[httpx.Request, httpx.Response, None]:
        """Inject the current Bearer token into the request Authorization header."""
        request.headers["Authorization"] = f"Bearer {self._dispenser.access_token.token}"
        yield request
