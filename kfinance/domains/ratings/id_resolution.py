import httpx

from kfinance.domains.ratings.ratings_models import EntityIdResp


async def resolve_entities(identifiers: list[str], httpx_client: httpx.AsyncClient) -> EntityIdResp:
    """Resolve one or more identifiers to id triples using the resolve_entities endpoint."""

    resp = await httpx_client.post(
        url="/ratings/resolve_entities/", json=dict(identifiers=identifiers)
    )
    resp.raise_for_status()
    resp_json = resp.json()
    return EntityIdResp.model_validate(resp_json)
