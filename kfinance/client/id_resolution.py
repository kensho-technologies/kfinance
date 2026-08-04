from __future__ import annotations

import httpx

from kfinance.client.models.dataset_filter_models import DatasetFilter
from kfinance.domains.companies.company_models import UnifiedIdTripleResponse


async def unified_fetch_id_triples(
    identifiers: list[str],
    httpx_client: httpx.AsyncClient,
    datasets_filter: list[DatasetFilter] | None = None,
    include_countries: bool = False,
) -> UnifiedIdTripleResponse:
    """Resolve one or more identifiers to id triples using the unified (/ids) endpoint.

    Args:
        identifiers: List of identifiers to resolve (tickers, ISINs, CUSIPs, company names, etc.)
        httpx_client: The async HTTP client configured for the kfinance server.
        datasets_filter: Optional list of LFA dataset filters to scope entity resolution.
        include_countries: When True, also resolves ISO 3166-1 alpha-3 country codes to
            sovereign entity IDs. Used by the Ratings dataset for sovereign entity resolution.
            Defaults to False.
    """
    request_body: dict = dict(identifiers=identifiers)
    if datasets_filter is not None:
        request_body["datasets_filter"] = [df.value for df in datasets_filter]
    if include_countries:
        request_body["include_countries"] = True

    resp = await httpx_client.post(url="/ids", json=request_body)
    resp.raise_for_status()
    resp_json = resp.json()
    return UnifiedIdTripleResponse.model_validate(resp_json)
