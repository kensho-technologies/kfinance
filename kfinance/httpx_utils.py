import asyncio
import atexit
from typing import Any, Generator

import httpx
from httpx import Request, Response

from kfinance.client.fetch import KFinanceApiClient


class KfinanceBearerAuth(httpx.Auth):
    def __init__(self, api_client: KFinanceApiClient) -> None:
        """"""
        self._api_client = api_client

    def auth_flow(self, request: httpx.Request) -> Generator[Request, Response, None]:
        """Inject access token into auth header"""
        request.headers["Authorization"] = f"Bearer {self._api_client.access_token}"
        yield request


class KfinanceHttpxClient(httpx.AsyncClient):
    """httpx.AsyncClient subclass that automatically prefixes URLs with a base URL and auto-registers cleanup."""

    def __init__(self, api_client: KFinanceApiClient) -> None:
        """"""
        super().__init__()
        self.auth = KfinanceBearerAuth(api_client=api_client)
        self._kfinance_base_url: str = f"{api_client.api_host}/api/v1"

        # Auto-register cleanup on exit
        atexit.register(self._cleanup_on_exit)

    def _cleanup_on_exit(self) -> None:
        """Clean up the httpx client on process exit."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(self.aclose())
            else:
                asyncio.run(self.aclose())
        except:  # noqa:E722
            pass  # Process is shutting down

    def _build_url(self, url: str) -> str:
        """Build the full URL by prepending base_url to relative URLs."""
        # If URL is already absolute (has scheme), return as-is
        if url.startswith(("http://", "https://")):
            return url
        return f"{self._kfinance_base_url}/{url.lstrip('/')}"

    async def request(self, method: str, url: str, **kwargs: Any) -> httpx.Response:  # type: ignore[override]
        """Override request to prepend base_url to relative URLs."""
        return await super().request(method=method, url=self._build_url(url), **kwargs)
