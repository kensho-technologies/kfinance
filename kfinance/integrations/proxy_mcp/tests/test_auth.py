from respx import Router

from kfinance.integrations.proxy_mcp.auth import Cache, ClientAccessToken, RefreshTokenDispenser


def test_refresh_token_sent_in_post_body(httpx2_mock: Router) -> None:
    """
    WHEN the proxy's RefreshTokenDispenser exchanges its refresh token
    THEN the refresh token is sent in a POST body, never in the URL

    A token in the URL ends up in server access logs and in httpx2's INFO log line.
    """
    refresh_url = "https://kfinance.kensho.com/oauth2/refresh"
    route = httpx2_mock.post(refresh_url, json={"refresh_token": "fake_refresh_token"}).respond(
        json={"access_token": "fake_access_token"}
    )
    dispenser = RefreshTokenDispenser(
        refresh_token="fake_refresh_token",
        refresh_url=refresh_url,
        cache=Cache[ClientAccessToken](),
        access_token_cache_key="test",
    )

    assert dispenser.refresh_access_token().token == "fake_access_token"
    assert "fake_refresh_token" not in str(route.calls.last.request.url)
