from dataclasses import dataclass
from typing import Protocol, Hashable

from kfinance.constants import IdentificationTriple, COMPANY_ID_PREFIX
from kfinance.fetch import KFinanceApiClient


class CompanyIdentifier(Protocol, Hashable):

    def fetch_company_id(self, api_client: KFinanceApiClient) -> int:
        ...

    def fetch_security_id(self, api_client: KFinanceApiClient) -> int:
        ...

    def fetch_trading_item_id(self, api_client: KFinanceApiClient) -> int:
        ...

@dataclass
class Identifier(CompanyIdentifier):

    identifier: str
    _id_triple: IdentificationTriple | None = None

    def __str__(self) -> str:
        return self.identifier

    def __hash__(self):
        return hash(self.identifier)

    def fetch_id_triple(self, api_client: KFinanceApiClient) -> IdentificationTriple:
        if self._id_triple is None:
            id_triple_resp = api_client.fetch_id_triple(identifier=self.identifier)
            self._id_triple = IdentificationTriple(
                trading_item_id=id_triple_resp["trading_item_id"],
                security_id=id_triple_resp["security_id"],
                company_id=id_triple_resp["company_id"],
            )
        return self._id_triple

    def fetch_company_id(self, api_client: KFinanceApiClient) -> int:
        return self.fetch_id_triple(api_client).company_id

    def fetch_security_id(self, api_client: KFinanceApiClient) -> int:
        return self.fetch_id_triple(api_client).security_id

    def fetch_trading_item_id(self, api_client: KFinanceApiClient) -> int:
        return self.fetch_id_triple(api_client).trading_item_id

@dataclass
class CompanyId(CompanyIdentifier):

    company_id: int

    def __str__(self) -> str:
        return f"{COMPANY_ID_PREFIX}{self.company_id}"

    def __hash__(self) -> int:
        return hash(self.company_id)

    def fetch_company_id(self, api_client: KFinanceApiClient) -> int:
        return self.company_id

    def fetch_security_id(self, api_client: KFinanceApiClient) -> int:
        security_resp = api_client.fetch_primary_security(company_id=self.company_id)
        return security_resp["primary_security"]

    def fetch_trading_item_id(self, api_client: KFinanceApiClient) -> int:
        trading_item_resp = api_client.fetch_primary_trading_item(
            security_id=self.fetch_security_id(api_client=api_client)
        )
        return trading_item_resp["primary_trading_item"]

def parse_identifiers(identifiers: list[str]) -> list[CompanyIdentifier]:

    parsed_identifiers = []
    for identifier in identifiers:
        if identifier.startswith(COMPANY_ID_PREFIX):
            parsed_identifiers.append(CompanyId(
                company_id=int(identifier[len(COMPANY_ID_PREFIX):]),
            ))
        else:
            parsed_identifiers.append(Identifier(identifier=identifier))

    return parsed_identifiers
