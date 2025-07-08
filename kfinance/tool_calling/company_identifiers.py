from dataclasses import dataclass
from typing import Hashable, Protocol

from kfinance.batch_request_handling import Task, process_tasks_in_thread_pool_executor
from kfinance.fetch import KFinanceApiClient
from kfinance.models.company_models import COMPANY_ID_PREFIX
from kfinance.models.id_models import IdentificationTriple


class CompanyIdentifier(Protocol, Hashable):
    """A CompanyIdentifier is an identifier that can be resolved to a company, security, or trading item id.

    The two current identifiers are:
    - Ticker/CUSIP/ISIN (resolve through ID triple)
    - company id (from tools like business relationships)

    These identifiers both have ways of fetching company, security, and trading
    item ids but the paths differ, so this protocol defines the functional requirements
    and leaves the implementation to sub classes.
    """

    def fetch_company_id(self, api_client: KFinanceApiClient) -> int:
        """Return the company_id associated with the CompanyIdentifier."""

    def fetch_security_id(self, api_client: KFinanceApiClient) -> int:
        """Return the security_id associated with the CompanyIdentifier."""

    def fetch_trading_item_id(self, api_client: KFinanceApiClient) -> int:
        """Return the trading_item_id associated with the CompanyIdentifier."""


@dataclass
class Identifier(CompanyIdentifier):
    """An identifier (ticker, CUSIP, ISIN), which can be resolved to company, security, or trading item id.

    The resolution happens by fetching the id triple.
    """

    identifier: str
    _id_triple: IdentificationTriple | None = None

    def __str__(self) -> str:
        return self.identifier

    def __hash__(self) -> int:
        return hash(self.identifier)

    def _fetch_id_triple(self, api_client: KFinanceApiClient) -> IdentificationTriple:
        if self._id_triple is None:
            id_triple_resp = api_client.fetch_id_triple(identifier=self.identifier)
            self._id_triple = IdentificationTriple(
                trading_item_id=id_triple_resp["trading_item_id"],
                security_id=id_triple_resp["security_id"],
                company_id=id_triple_resp["company_id"],
            )
        return self._id_triple

    def fetch_company_id(self, api_client: KFinanceApiClient) -> int:
        """Return the company_id associated with the Identifier."""
        return self._fetch_id_triple(api_client).company_id

    def fetch_security_id(self, api_client: KFinanceApiClient) -> int:
        """Return the security_id associated with the Identifier."""
        return self._fetch_id_triple(api_client).security_id

    def fetch_trading_item_id(self, api_client: KFinanceApiClient) -> int:
        """Return the trading_item_id associated with the Identifier."""
        return self._fetch_id_triple(api_client).trading_item_id


@dataclass
class CompanyId(CompanyIdentifier):
    """A company id, which can be resolved to security and trading item id.

    The resolution happens by fetching the primary security and trading item id
    associated with the company id.
    """

    company_id: int

    def __str__(self) -> str:
        return f"{COMPANY_ID_PREFIX}{self.company_id}"

    def __hash__(self) -> int:
        return hash(self.company_id)

    def fetch_company_id(self, api_client: KFinanceApiClient) -> int:
        """Return the company_id."""
        return self.company_id

    def fetch_security_id(self, api_client: KFinanceApiClient) -> int:
        """Return the security_id associated with the CompanyId."""
        security_resp = api_client.fetch_primary_security(company_id=self.company_id)
        return security_resp["primary_security"]

    def fetch_trading_item_id(self, api_client: KFinanceApiClient) -> int:
        """Return the trading_item_id associated with the CompanyId."""
        trading_item_resp = api_client.fetch_primary_trading_item(
            security_id=self.fetch_security_id(api_client=api_client)
        )
        return trading_item_resp["primary_trading_item"]


def parse_identifiers(identifiers: list[str]) -> list[CompanyIdentifier]:
    """Return a list of CompanyIdentifier based on a list of string identifiers."""

    parsed_identifiers: list[CompanyIdentifier] = []
    for identifier in identifiers:
        if identifier.startswith(COMPANY_ID_PREFIX):
            parsed_identifiers.append(
                CompanyId(
                    company_id=int(identifier[len(COMPANY_ID_PREFIX) :]),
                )
            )
        else:
            parsed_identifiers.append(Identifier(identifier=identifier))

    return parsed_identifiers


def fetch_company_ids_from_identifiers(
    identifiers: list[CompanyIdentifier], api_client: KFinanceApiClient
) -> dict[CompanyIdentifier, int]:
    """Resolve a list of CompanyIdentifier to the corresponding company_ids."""

    tasks = [
        Task(
            func=identifier.fetch_company_id,
            result_key=identifier,
            kwargs=dict(api_client=api_client),
        )
        for identifier in identifiers
    ]
    return process_tasks_in_thread_pool_executor(api_client=api_client, tasks=tasks)


def fetch_security_ids_from_identifiers(
    identifiers: list[CompanyIdentifier], api_client: KFinanceApiClient
) -> dict[CompanyIdentifier, int]:
    """Resolve a list of CompanyIdentifier to the corresponding security_ids."""

    tasks = [
        Task(
            func=identifier.fetch_security_id,
            result_key=identifier,
            kwargs=dict(api_client=api_client),
        )
        for identifier in identifiers
    ]
    return process_tasks_in_thread_pool_executor(api_client=api_client, tasks=tasks)


def fetch_trading_item_ids_from_identifiers(
    identifiers: list[CompanyIdentifier], api_client: KFinanceApiClient
) -> dict[CompanyIdentifier, int]:
    """Resolve a list of CompanyIdentifier to the corresponding trading_item_ids."""
    tasks = [
        Task(
            func=identifier.fetch_trading_item_id,
            result_key=identifier,
            kwargs=dict(api_client=api_client),
        )
        for identifier in identifiers
    ]
    return process_tasks_in_thread_pool_executor(api_client=api_client, tasks=tasks)
