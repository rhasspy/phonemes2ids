"""Setup file for phonemes2ids"""
import os
from pathlib import Path

import setuptools

this_dir = Path(__file__).parent
module_dir = this_dir / "phonemes2ids"

# -----------------------------------------------------------------------------

# Load README in as long description
long_description: str = ""
readme_path = this_dir / "README.md"
if readme_path.is_file():
    long_description = readme_path.read_text()

version_path = module_dir / "VERSION"
with open(version_path, "r") as version_file:
    version = version_file.read().strip()

# -----------------------------------------------------------------------------

setuptools.setup(
    name="phonemes2ids",
    version=version,
    description="Convert phonemes to integer ids",
    author="Michael Hansen",
    author_email="mike@rhasspy.org",
    url="https://github.com/rhasspy/phonemes2ids",
    packages=setuptools.find_packages(),
    package_data={"phonemes2ids": ["VERSION", "py.typed"]},
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "License :: OSI Approved :: MIT License",
    ],
    long_description=long_description,
    long_description_content_type="text/markdown",
)
