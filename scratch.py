import asyncio
import os

from kfinance.client.kfinance import Client
from kfinance.domains.business_relationships.business_relationship_models import BusinessRelationshipType
from kfinance.domains.business_relationships.business_relationship_tools import \
    GetBusinessRelationshipFromIdentifiersArgs, GetBusinessRelationshipFromIdentifiers


args = GetBusinessRelationshipFromIdentifiersArgs(
    identifiers=["SPGI"],
    business_relationship=BusinessRelationshipType.supplier,
)

sync_client = Client(refresh_token=os.environ["KFINANCE_PROD_REFRESH_KEY"])
async_client = Client(refresh_token=os.environ["KFINANCE_PROD_REFRESH_KEY"])

def run_sync():
    tool = GetBusinessRelationshipFromIdentifiers(kfinance_client=sync_client)
    sync_resp = tool.run(args.model_dump(mode="json"))
    print("sync")
    return sync_resp

async def run_async_twice():
    tool = GetBusinessRelationshipFromIdentifiers(kfinance_client=async_client)
    async_resp1 = await tool.ainvoke(args.model_dump(mode="json"))
    async_resp2 = await tool.ainvoke(args.model_dump(mode="json"))
    print("async")
    return async_resp1, async_resp2


# Sync calls can be run multiple times (no async loop issues)
sync_res1 = run_sync()
sync_res2 = run_sync()

# Event loop gets closed after asyncio.run, so we run the tool twice in the function
async_res1, async_res2 = asyncio.run(run_async_twice())

# Sync calls can still be run after async calls
sync_res3 = run_sync()
sync_res4 = run_sync()

assert sync_res1 == sync_res2 == sync_res3 == sync_res4 == async_res1 == async_res2

