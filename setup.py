from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="free-web-search",
    version="7.0.0",
    author="wd041216-bit",
    author_email="",
    description="Zero-cost, privacy-first web search for AI agents",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/wd041216-bit/free-web-search",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Internet :: WWW/HTTP :: Indexing/Search",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    install_requires=[
        "urllib3>=1.26.0",
        "beautifulsoup4>=4.9.0",
        "lxml>=4.6.0",
        "ddgs>=0.1.0",
    ],
    extras_require={
        "dynamic": ["playwright>=1.40.0"],
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "free-web-search=scripts.search_web:main",
            "free-web-browse=scripts.browse_page:main",
        ],
    },
)
