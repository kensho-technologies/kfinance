from requests_mock import Mocker

from kfinance.client.kfinance import Client
from kfinance.conftest import SPGI_COMPANY_ID
from kfinance.domains.business_relationships.business_relationship_models import (
    BusinessRelationshipType,
)
from kfinance.domains.business_relationships.business_relationship_tools import (
    GetBusinessRelationshipFromIdentifiers,
    GetBusinessRelationshipFromIdentifiersArgs,
    GetBusinessRelationshipFromIdentifiersResp,
)


class TestGetBusinessRelationshipFromIdentifiers:
    def test_get_business_relationship_from_identifiers(
        self, requests_mock: Mocker, mock_client: Client
    ):
        """
        GIVEN the GetBusinessRelationshipFromIdentifiers tool
        WHEN we request suppliers for SPGI and a non-existent company
        THEN we get back the SPGI suppliers and an error message
        """
        supplier_resp = {
            "current": [{"company_id": 883103, "company_name": "CRISIL Limited"}],
            "previous": [
                {"company_id": 472898, "company_name": "Morgan Stanley"},
                {"company_id": 8182358, "company_name": "Eloqua, Inc."},
            ],
        }
        expected_result = GetBusinessRelationshipFromIdentifiersResp.model_validate(
            {
                "business_relationship": "supplier",
                "results": {
                    "SPGI": {
                        "current": [{"company_id": 883103, "company_name": "CRISIL Limited"}],
                        "previous": [
                            {"company_id": 472898, "company_name": "Morgan Stanley"},
                            {"company_id": 8182358, "company_name": "Eloqua, Inc."},
                        ],
                    }
                },
                "errors": [
                    "No identification triple found for the provided identifier: NON-EXISTENT of type: ticker"
                ],
            }
        )

        requests_mock.get(
            url=f"https://kfinance.kensho.com/api/v1/relationship/{SPGI_COMPANY_ID}/supplier",
            json=supplier_resp,
        )

        tool = GetBusinessRelationshipFromIdentifiers(kfinance_client=mock_client)
        args = GetBusinessRelationshipFromIdentifiersArgs(
            identifiers=["SPGI", "non-existent"],
            business_relationship=BusinessRelationshipType.supplier,
        )
        resp = tool.run(args.model_dump(mode="json"))
        assert resp == expected_result
