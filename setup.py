from setuptools import setup, find_packages

setup(
    name="langchain-auragrid",
    version="0.2.0",
    description="LangChain tool for AurAgrid: Bitcoin/Lightning data (L402) and free U.S. public-domain feeds, with signed responses.",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="AurAgrid Corp",
    author_email="auragridcorp@gmail.com",
    url="https://github.com/auragridcorp-rgb/langchain-auragrid",
    packages=find_packages(),
    install_requires=[
        "langchain-core>=0.2.0",
        "pydantic>=2.0.0",
        "requests>=2.28.0",
        "auragrid-mcp>=0.2.0",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
)
