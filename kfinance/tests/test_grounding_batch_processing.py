import pytest
from concurrent.futures import ThreadPoolExecutor, as_completed
from requests_mock import Mocker

from kfinance.kfinance import Client
from kfinance.tool_calling import GetInfoFromIdentifier

class TestGetEndpointsFromToolCallsWithGroundingMultiThreaded:
    def test_get_info_from_identifier_with_grounding_multithreaded(
        self, mock_client: Client, requests_mock: Mocker
    ):
        """
        GIVEN multiple KfinanceTool tools running concurrently
        WHEN we run the tools with `run_with_grounding` using ThreadPoolExecutor
        THEN we get back all endpoint urls from all threads in addition to the usual tool responses.
        """
        
        # Test data for multiple companies
        test_companies = [
            {
                "identifier": "SPGI",
                "company_id": 21719,
                "resp_data": "{'name': 'S&P Global Inc.', 'status': 'Operating'}",
                "expected_endpoints": [
                    "https://kfinance.kensho.com/api/v1/id/SPGI",
                    "https://kfinance.kensho.com/api/v1/info/21719",
                ]
            },
            {
                "identifier": "AAPL",
                "company_id": 24937,
                "resp_data": "{'name': 'Apple Inc.', 'status': 'Operating'}",
                "expected_endpoints": [
                    "https://kfinance.kensho.com/api/v1/id/AAPL",
                    "https://kfinance.kensho.com/api/v1/info/24937",
                ]
            },
            {
                "identifier": "GOOGL",
                "company_id": 29096,
                "resp_data": "{'name': 'Alphabet Inc.', 'status': 'Operating'}",
                "expected_endpoints": [
                    "https://kfinance.kensho.com/api/v1/id/GOOGL",
                    "https://kfinance.kensho.com/api/v1/info/29096",
                ]
            },
            {
                "identifier": "MSFT",
                "company_id": 21835,
                "resp_data": "{'name': 'Microsoft Corporation', 'status': 'Operating'}",
                "expected_endpoints": [
                    "https://kfinance.kensho.com/api/v1/id/MSFT",
                    "https://kfinance.kensho.com/api/v1/info/21835",
                ]
            },
        ]

        # Mock all the API endpoints
        for company in test_companies:
            # Mock the info endpoint
            requests_mock.get(
                url=f"https://kfinance.kensho.com/api/v1/info/{company['company_id']}",
                json=company["resp_data"],
            )

        # Create tools for each company
        tools = [GetInfoFromIdentifier(kfinance_client=mock_client) for _ in test_companies]
        
        def run_tool_with_identifier(tool: GetInfoFromIdentifier, identifier: str):
            """Helper function to run a single tool with its identifier"""
            return tool.run_with_grounding(identifier=identifier)

        # Execute tools concurrently using ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=4) as executor:
            # Prepare a dictionary to hold future results and their associated companies
            futures = {}
            
            # Submit tasks to the executor
            for tool, company in zip(tools, test_companies):
                identifier = company["identifier"]
                future = executor.submit(run_tool_with_identifier, tool, identifier)
                futures[future] = company
            
            # Collect results as they complete
            results = []
            for future in as_completed(futures):  # Fixed variable name from future_to_company to futures
                company = futures[future]  # Get the associated company
                try:
                    result = future.result()  # Get the result of the future
                    results.append((company, result))  # Append the result and company to the results list
                except Exception as exc:
                    pytest.fail(f'Tool for {company["identifier"]} generated an exception: {exc}')
            # Verify we got results from all threads
            assert len(results) == len(test_companies), "Should have results from all threads"

        # Collect all expected endpoints and actual endpoints
        all_expected_endpoints = []
        all_actual_endpoints = []
        
        for company, result in results:
            print("individual endpoint results:", result["endpoint_urls"])
            # Verify individual tool response structure
            assert "data" in result, f"Response for {company['identifier']} should have 'data' key"
            assert "endpoint_urls" in result, f"Response for {company['identifier']} should have 'endpoint_urls' key"
            
            # Verify individual tool data
            assert result["data"] == company["resp_data"], f"Data mismatch for {company['identifier']}"
            
            # Collect endpoints
            all_expected_endpoints.extend(company["expected_endpoints"])
            all_actual_endpoints.extend(result["endpoint_urls"])

        print("collected endpoints:", all_actual_endpoints)

        # Verify all endpoints were collected across all threads
        assert len(all_actual_endpoints) == len(all_expected_endpoints), \
            f"Expected {len(all_expected_endpoints)} endpoints, got {len(all_actual_endpoints)}"
        
        # Verify all expected endpoints are present (order might vary due to threading)
        assert set(all_actual_endpoints) == set(all_expected_endpoints), \
            f"Endpoint mismatch. Expected: {set(all_expected_endpoints)}, Got: {set(all_actual_endpoints)}"
