# Copyright 2025-present Kensho Technologies, LLC.
# Package metadata is located in pyproject.toml

from distutils.core import setup  # pylint: disable=deprecated-module

setup(
    name="kfinance",
    packages=["kfinance"],
    version="0.99.0",
    description="",
    author="Luke Brown",
    author_email="luke.brown@kensho.com",
    url="https://github.com/kensho-technologies/kfinance",
    download_url="https://github.com/kensho-technologies/kfinance/archive/refs/tags/v_0_99_0.tar.gz",  # noqa:E501
    keywords=["kFinance", "Python Toolkit"],
    install_requires=[
        "langchain-core",
        "numpy",
        "pandas",
        "pillow",
        "pyjwt",
        "python-dateutil",
        "requests",
        "strenum",
        "types-requests",
        "urllib3",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
)
