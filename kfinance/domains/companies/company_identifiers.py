from dataclasses import dataclass
from typing import Hashable, Protocol

from kfinance.client.batch_request_handling import Task, process_tasks_in_thread_pool_executor
from kfinance.client.fetch import KFinanceApiClient
from kfinance.domains.companies.company_models import COMPANY_ID_PREFIX, IdentificationTriple


class CompanyIdentifier(Protocol, Hashable):
    """A CompanyIdentifier is an identifier that can be resolved to a company, security, or trading item id.

    The two current identifiers are:
    - Ticker/CUSIP/ISIN (resolve through ID triple)
    - company id (from tools like business relationships)

    These identifiers both have ways of fetching company, security, and trading
    item ids but the paths differ, so this protocol defines the functional requirements
    and leaves the implementation to sub classes.
    """

    api_client: KFinanceApiClient

    def fetch_company_id(self) -> int:
        """Return the company_id associated with the CompanyIdentifier."""

    def fetch_security_id(self) -> int:
        """Return the security_id associated with the CompanyIdentifier."""

    def fetch_trading_item_id(self) -> int:
        """Return the trading_item_id associated with the CompanyIdentifier."""


@dataclass
class Identifier(CompanyIdentifier):
    """An identifier (ticker, CUSIP, ISIN), which can be resolved to company, security, or trading item id.

    The resolution happens by fetching the id triple.
    """

    identifier: str
    api_client: KFinanceApiClient
    _id_triple: IdentificationTriple | None = None

    def __str__(self) -> str:
        return self.identifier

    def __hash__(self) -> int:
        return hash(self.identifier)

    @property
    def id_triple(self) -> IdentificationTriple:
        """Return the id triple of the company."""
        if self._id_triple is None:
            id_triple_resp = self.api_client.fetch_id_triple(identifier=self.identifier)
            self._id_triple = IdentificationTriple(
                trading_item_id=id_triple_resp["trading_item_id"],
                security_id=id_triple_resp["security_id"],
                company_id=id_triple_resp["company_id"],
            )
        return self._id_triple

    def fetch_company_id(self) -> int:
        """Return the company_id associated with the Identifier."""
        return self.id_triple.company_id

    def fetch_security_id(self) -> int:
        """Return the security_id associated with the Identifier."""
        return self.id_triple.security_id

    def fetch_trading_item_id(self) -> int:
        """Return the trading_item_id associated with the Identifier."""
        return self.id_triple.trading_item_id


@dataclass
class CompanyId(CompanyIdentifier):
    """A company id, which can be resolved to security and trading item id.

    The resolution happens by fetching the primary security and trading item id
    associated with the company id.
    """

    company_id: int
    api_client: KFinanceApiClient
    _security_id: int | None = None
    _trading_item_id: int | None = None

    def __str__(self) -> str:
        return f"{COMPANY_ID_PREFIX}{self.company_id}"

    def __hash__(self) -> int:
        return hash(self.company_id)

    def fetch_company_id(self) -> int:
        """Return the company_id."""
        return self.company_id

    def fetch_security_id(self) -> int:
        """Return the security_id associated with the CompanyId."""
        if self._security_id is None:
            security_resp = self.api_client.fetch_primary_security(company_id=self.company_id)
            self._security_id = security_resp["primary_security"]
        return self._security_id

    def fetch_trading_item_id(self) -> int:
        """Return the trading_item_id associated with the CompanyId."""
        if self._trading_item_id is None:
            trading_item_resp = self.api_client.fetch_primary_trading_item(
                security_id=self.fetch_security_id()
            )
            self._trading_item_id = trading_item_resp["primary_trading_item"]
        return self._trading_item_id


def parse_identifiers(
    identifiers: list[str], api_client: KFinanceApiClient
) -> list[CompanyIdentifier]:
    """Return a list of CompanyIdentifier based on a list of string identifiers."""

    parsed_identifiers: list[CompanyIdentifier] = []
    for identifier in identifiers:
        if identifier.startswith(COMPANY_ID_PREFIX):
            parsed_identifiers.append(
                CompanyId(
                    company_id=int(identifier[len(COMPANY_ID_PREFIX) :]), api_client=api_client
                )
            )
        else:
            parsed_identifiers.append(Identifier(identifier=identifier, api_client=api_client))

    return parsed_identifiers


def fetch_company_ids_from_identifiers(
    identifiers: list[CompanyIdentifier], api_client: KFinanceApiClient
) -> dict[CompanyIdentifier, int]:
    """Resolve a list of CompanyIdentifier to the corresponding company_ids."""

    tasks = [
        Task(
            func=identifier.fetch_company_id,
            result_key=identifier,
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
        )
        for identifier in identifiers
    ]
    return process_tasks_in_thread_pool_executor(api_client=api_client, tasks=tasks)
