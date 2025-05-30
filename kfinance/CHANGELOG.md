# Changelog

## v2.2.5
- Add parsing for relationship response with name

## v2.2.4
- Add segments as llm tools

## v2.2.3
- Change segments return type to nested dictionary

## v2.2.2
- Add segments

## v2.2.1
- Make number of employees optional to reflect backend changes

## v2.2.0
- Replace get company id, get security id, get trading item id tools with resolve identifier tool

## v2.1.2
- Allow batch executor to handle multiple requests

## v2.1.1
- Use cachetools cache

## v2.1.0
- Filter llm tools by user permissions

## v2.0.2
- Add Client.tickers() method for ticker industry filters for ISRCS and GICS

## v2.0.1
- Fix readthedocs integration for llm tools.

## v2.0.0
- Refactor llm tools to use langchain `BaseTool`.

## v1.2.2
- Add tabulate and pydantic as dependencies

## v1.2.1
- Add fetch for industry_code, industry_classification and gics_code.

## v1.2.0
- Add batch requests for iterable classes

## v1.1.0
- Add market cap, TEV, and shares outstanding

## v1.0.3
- Fix typo for get_history_metadata_from_identifier.

## v1.0.2
- Relaxing requirements for urllib3 dependency.

## v1.0.1
- Correct installation instructions in README.

## v1.0.0
- Initial public release

## v0.99.1
- Update llm tools to use identifier instead of ticker

## v0.99.0
- Initial KFinance Client
