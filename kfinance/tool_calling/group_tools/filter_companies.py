from textwrap import dedent
from typing import Type

from pydantic import BaseModel, Field

from kfinance.constants import IdentificationTriple, Permission, ToolMode
from kfinance.kfinance import Tickers
from kfinance.tool_calling.shared_models import KfinanceTool


class FilterCompaniesArgs(BaseModel):
    # no description because the description for enum fields comes from the enum docstring.
    country_iso_code: str | None = Field(
        description="The ISO 3166-1 Alpha-2 or Alpha-3 code that represent the primary country where the company is based.",
        default=None,
    )
    state_iso_code: str | None = Field(
        description="The ISO 3166-2 Alpha-2 code that represents the primary subdivision of the country the firm the based in. If a state_iso_code is passed, a country_iso_code has to be passed as well.",
        default=None,
    )
    gics_industry: int | None = Field(
        description="The GICS industry to filter on. Use the numeric code, not the industry name. For example, for 'Oil & Gas Drilling', pass 10101010.",
        default=None,
    )
    exchange_code: str | None = Field(
        description="The exchange on which the company is listed.", default=None
    )


class FilterCompanies(KfinanceTool):
    """Return companies that match the provided filters.

    This function is still highly experimental.
    - filtering is slow and often times out after 60s for large queries
    - follow-up queries can take a long time (e.g. fetching prices for up to 1000 companies)
    - filtering is incomplete, only GICS is currently supported for industries.
    """

    name: str = "filter_companies"
    description: str = dedent("""
        Return the companies that match all of the defined filters.

        - One of country_iso_code, gics_industry, or exchange_code must be supplied.
        """).strip()
    args_schema: Type[BaseModel] = FilterCompaniesArgs
    required_permission: Permission | None = None
    tool_modes: set[ToolMode] = {ToolMode.GROUP}

    def _run(
        self,
        country_iso_code: str | None = None,
        state_iso_code: str | None = None,
        gics_industry: str | None = None,
        exchange_code: str | None = None,
    ) -> list[str]:
        tickers = self.kfinance_client.tickers(
            country_iso_code=country_iso_code,
            state_iso_code=state_iso_code,
            exchange_code=exchange_code,
            gics=gics_industry,
        )

        # Limit responses to 1000 tickers
        tickers = Tickers(
            kfinance_api_client=self.kfinance_client.kfinance_api_client,
            id_triples=[
                IdentificationTriple(
                    company_id=t.company_id,
                    security_id=t.security_id,
                    trading_item_id=t.trading_item_id,
                )
                for t in list(tickers)[:1000]
            ],
        )

        # Fetch all company infos in a batch to obtain company names

        return [
            str(
                dict(
                    name=ticker.name,
                    company_id=ticker.company_id,
                    security_id=ticker.security_id,
                    trading_item_id=ticker.trading_item_id,
                )
            )
            for ticker in tickers
        ]
