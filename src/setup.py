# setup.py
from setuptools import setup, find_packages

setup(
    name="djanalyzer",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "librosa",    # e qualsiasi altra dipendenza
        "numpy",
    ],
)
