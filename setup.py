from setuptools import find_packages, setup

setup(
    name="AppStarter",
    version="0.0.1",
    description="AppStarter for OpenVerseProject",
    author="Javicle",
    author_email="qubackx@gmail.com",
    packages=find_packages(),
    package_data={"tools_openverse.common": ["py.typed"]},
    include_package_data=True,
    install_requires=[
        "fastapi",
        "setuptools",
        "rich",
        "sqlalchemy",
        "opentelemetry-instrumentation-fastapi",
        "opentelemetry-sdk",
        "opentelemetry-exporter-otlp-proto-http",
    ],
)
