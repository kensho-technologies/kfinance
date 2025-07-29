from pathlib import Path
import subprocess
import sys
from textwrap import dedent
import uuid

from nbconvert.preprocessors import ExecutePreprocessor
import nbformat
import pytest


@pytest.fixture(scope="session")
def jupyter_kernel_name() -> str:
    """Create a jupyter kernel for a test run and yield its name.

    The kernel gets removed at the end of the test run.
    """

    kernel_name = f"test-kfinance-kernel-{uuid.uuid4().hex[:8]}"

    # Install a new kernel pointing to the current interpreter.
    subprocess.run(
        [
            sys.executable,
            "-m",
            "ipykernel",
            "install",
            "--user",
            "--name",
            kernel_name,
            "--display-name",
            f"Python ({kernel_name})",
        ],
        check=True,
    )

    yield kernel_name

    # Remove the kernel after the test.
    subprocess.run(
        [sys.executable, "-m", "jupyter", "kernelspec", "uninstall", "-f", kernel_name], check=True
    )


def test_run_notebook(jupyter_kernel_name: str):
    """
    GIVEN the basic_usage.ipynb notebook
    WHEN the notebook gets run with a mock client and mock responses
    THEN all cells of the notebook complete without errors.
    """

    # Create a replacement startup cell for the normal notebook client init.
    # This cell contains:
    # - setup of a mock client
    # - mocks for all calls made by the client while executing the notebook
    startup_cell_code = dedent("""
        from datetime import datetime
        from kfinance.client.kfinance import Client
        kfinance_client = Client(refresh_token="foo")
        api_client = kfinance_client.kfinance_api_client
        # Set access token so that the client doesn't try to fetch it.
        api_client._access_token = "foo"
        api_client._access_token_expiry = datetime(2100, 1, 1).timestamp()

        # Mock out all necessary requests with requests_mock
        import requests_mock
        mocker = requests_mock.Mocker()
        mocker.start()

        id_triple_resp = {
            "trading_item_id": 2629108,
            "security_id": 2629107,
            "company_id": 21719
        }

        # spgi = kfinance_client.ticker("SPGI")
        mocker.get(
            url="https://kfinance.kensho.com/api/v1/id/SPGI",
            json=id_triple_resp
        )

        mocker.get(
            url="https://kfinance.kensho.com/api/v1/info/21719",
            json={"name": "S&P Global Inc."}
        )

        balance_sheet_resp = {
            "statements": {
                "2022Q3": {"Cash And Equivalents": "1387000000.000000"},
                "2022Q4": {"Cash And Equivalents": "1286000000.000000"}
            }
        }

        # spgi.balance_sheet()
        mocker.get(
            url="https://kfinance.kensho.com/api/v1/statements/21719/balance_sheet/none/none/none/none/none",
            json=balance_sheet_resp
        )

        # spgi.balance_sheet(period_type=PeriodType.annual, start_year=2010, end_year=2019)
        mocker.get(
            url="https://kfinance.kensho.com/api/v1/statements/21719/balance_sheet/annual/2010/2019/none/none",
            json=balance_sheet_resp
        )

        # kfinance_client.ticker("JPM").balance_sheet()
        # (leads to fetching SPGI balance sheet when requesting JPM because they return the same
        # company id)
        mocker.get(
            url="https://kfinance.kensho.com/api/v1/id/JPM",
            json=id_triple_resp
        )

        # spgi.net_income(period_type=PeriodType.annual, start_year=2010, end_year=2019)
        mocker.get(
            url="https://kfinance.kensho.com/api/v1/line_item/21719/net_income/annual/2010/2019/none/none",
            json={"line_item": {"2010": "828000000.000000"}}
        )

        prices_resp = {
            "currency": "USD",
            "prices": [
                {
                    "date": "2024-05-20",
                    "open": "439.540000",
                    "high": "441.570000",
                    "low": "437.000000",
                    "close": "437.740000",
                    "volume": "1080006"
                }
            ]
        }

        # spgi.history()
        mocker.get(
            url="https://kfinance.kensho.com/api/v1/pricing/2629108/none/none/day/adjusted",
            json=prices_resp
        )

        # spgi.history(
        #     periodicity=Periodicity.month,
        #     adjusted=False,
        #     start_date="2010-01-01",
        #     end_date="2019-12-31"
        # )
        mocker.get(
            url="https://kfinance.kensho.com/api/v1/pricing/2629108/2010-01-01/2019-12-31/month/unadjusted",
            json=prices_resp
        )

        # spgi.price_chart(
        #     periodicity=Periodicity.month,
        #     adjusted=False,
        #     start_date="2010-01-01",
        #     end_date="2019-12-31"
        # )
        mocker.get(
            url='https://kfinance.kensho.com/api/v1/price_chart/2629108/2010-01-01/2019-12-31/month/unadjusted',
            content=b"",
            headers={'Content-Type': 'image/png'}
        )
        # Mock out image_open so that we don't have to return an actual png.
        from unittest.mock import MagicMock
        import kfinance.client.kfinance
        kfinance.client.kfinance.image_open = MagicMock()
    """)

    # Load the notebook
    notebook_path = Path(
        Path(__file__).parent.parent.parent.parent, "example_notebooks", "basic_usage.ipynb"
    )
    with notebook_path.open() as f:
        nb = nbformat.read(f, as_version=4)

    # Set up the notebook executor
    ep = ExecutePreprocessor(timeout=600, kernel_name=jupyter_kernel_name)

    # Identify the start of the example section
    example_sections_heading = "## Example functions"
    examples_start_cell_id = None
    for idx, cell in enumerate(nb.cells):
        if cell["source"] == example_sections_heading:
            examples_start_cell_id = idx

    if not examples_start_cell_id:
        raise ValueError(
            f"Did not find a cell with content {example_sections_heading} that "
            f"indicates the start of the examples."
        )

    # Combine the startup cell with the start of the examples
    # i.e. toss everything before the examples start
    nb.cells = [nbformat.v4.new_code_cell(startup_cell_code)] + nb.cells[examples_start_cell_id:]

    # Run the notebook.
    # The test passes if the notebook runs without errors.
    ep.preprocess(nb, {"metadata": {"path": notebook_path.parent}})
