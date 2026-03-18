from setuptools import setup, find_namespace_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="free-web-search-ultimate",
    version="12.0.0",
    author="wd041216-bit",
    author_email="",
    description="Universal Search-First Knowledge Acquisition Plugin for LLMs (MCP + CLI-Anything)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/wd041216-bit/free-web-search-ultimate",
    packages=find_namespace_packages(include=["free_web_search*"]),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Internet :: WWW/HTTP :: Indexing/Search",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.10",
    install_requires=[
        "urllib3>=1.26.0",
        "beautifulsoup4>=4.9.0",
        "lxml>=4.6.0",
        "ddgs>=0.1.0",
        "mcp>=1.1.2",
    ],
    entry_points={
        "console_scripts": [
            "search-web=free_web_search.search_web:main",
            "browse-page=free_web_search.browse_page:main",
            "free-web-search-mcp=free_web_search.mcp_server:run",
        ],
    },
    package_data={
        "free_web_search": ["skills/*.md"],
    },
    include_package_data=True,
    zip_safe=False,
)
