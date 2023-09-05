from setuptools import setup, find_packages

# read the contents of your README file
from os import path

this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, "README.md"), encoding="utf-8") as f:
    long_description = f.read()


setup(
    name="tunneller",
    version="0.1.0",
    author="",
    author_email="",
    description="",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[""],
    entry_points={
        "console_scripts": [
            "tunneller=tunneller.tunnel:main",
        ],
    },
    classifiers=[  # https://pypi.org/classifiers
        "Programming Language :: Python :: 3",
    ],
)
