from unittest.mock import Mock

from kfinance.client.kfinance import Client, IdentificationTriple, Tickers


class TestTickers:
    def test_tickers(self, mock_client: Client):
        """
        WHEN the client requests tickers using multiple filters
        THEN only tickers matching all filter criteria are returned
        """
        ticker_1 = IdentificationTriple(company_id=1, security_id=1, trading_item_id=1)
        ticker_2 = IdentificationTriple(company_id=2, security_id=2, trading_item_id=2)
        ticker_3 = IdentificationTriple(company_id=3, security_id=3, trading_item_id=3)
        expected_intersection = Tickers(
            kfinance_api_client=mock_client.kfinance_api_client, id_triples=[ticker_2]
        )
        # tickers() calls both fetch_ticker_combined and fetch_ticker_from_industry_code so we set two different return values to test intersection()
        mock_client.kfinance_api_client.fetch_ticker_combined = Mock()
        mock_client.kfinance_api_client.fetch_ticker_combined.return_value = [ticker_1, ticker_2]
        mock_client.kfinance_api_client.fetch_ticker_from_industry_code = Mock()
        mock_client.kfinance_api_client.fetch_ticker_from_industry_code.return_value = [
            ticker_3,
            ticker_2,
        ]
        tickers_object = mock_client.tickers(
            country_iso_code="USA", state_iso_code="FL", sic="6141", gics="2419512"
        )
        # fetch_ticker_from_industry_code should be called once for SIC and GICS
        assert mock_client.kfinance_api_client.fetch_ticker_from_industry_code.call_count == 2
        # Only the common tickers are returned
        assert tickers_object == expected_intersection
