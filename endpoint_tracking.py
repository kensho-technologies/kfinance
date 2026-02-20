import asyncio
import os
import random

from kfinance.client.kfinance import Client
from kfinance.domains.business_relationships.business_relationship_models import BusinessRelationshipType
from kfinance.domains.business_relationships.business_relationship_tools import GetBusinessRelationshipFromIdentifiers, \
    GetBusinessRelationshipFromIdentifiersResp

client = Client(refresh_token=os.environ["KFINANCE_PROD_REFRESH_KEY"])
tool = GetBusinessRelationshipFromIdentifiers(kfinance_client=client)

async def run_grounding_task(task_id: int) -> None:
    """Run a single grounding task and return results with metadata."""

    identifier = random.choice(["MSFT", "SPGI"])
    relationship_type = random.choice(list(BusinessRelationshipType))

    print(f"Task {task_id}: Starting {identifier} -> {relationship_type}")

    result = await tool.run_with_endpoint_tracking(
        identifiers=[identifier],
        business_relationship=relationship_type
    )

    id_url = result["endpoint_urls"][0]
    assert id_url == 'https://kfinance.kensho.com/api/v1/ids'
    relationship_url = result["endpoint_urls"][1]

    print(f"Task {task_id}: Completed. Identifier: {identifier}. Relationship type: {relationship_type} "
          f"URL: {relationship_url}.")

    if identifier == "MSFT":
        assert "21835" in relationship_url
    else:
        assert "21719" in relationship_url
    assert relationship_type.value in relationship_url
    assert type(result["data"]) == GetBusinessRelationshipFromIdentifiersResp



async def run_with_tracking():
    tasks = [run_grounding_task(i) for i in range(10)]
    await asyncio.gather(*tasks, return_exceptions=True)

asyncio.run(run_with_tracking())