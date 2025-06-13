from setuptools import setup, find_packages

setup(
    name="homeassistant-aircontrolbase",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "aiohttp",
        "async_timeout",
    ],
) 