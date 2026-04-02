import httpx

from kfinance.domains.companies.company_models import UnifiedIdTripleResponse


async def unified_fetch_id_triples(
    identifiers: list[str], httpx_client: httpx.AsyncClient
) -> UnifiedIdTripleResponse:
    """Resolve one or more identifiers to id triples using the unified (/ids) endpoint."""

    resp = await httpx_client.post(url="/ids", json=dict(identifiers=identifiers))
    resp.raise_for_status()
    resp_json = resp.json()
    return UnifiedIdTripleResponse.model_validate(resp_json)
