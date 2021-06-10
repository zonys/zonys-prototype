import re
import setuptools

readme = ""
with open("README.md", encoding="utf-8") as handle:
    readme = handle.read()

setuptools.setup(
    name="zonys",
    version="0.2.0",
    description="Another container and execution environment manager for the FreeBSD operating system.",
    long_description=readme,
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(
        include=["zonys", "zonys.*"],
    ),
    author="Justus Flerlage",
    author_email="justus@sutsuj.com",
    url="https://github.com/zonys/zonys",
    entry_points={
        "console_scripts": [
            "z3s = zonys.cli:main"
        ]
    },
    install_requires=[
        "GitPython>=3.1",
        "Pygments>=2.9",
        "cerberus>=1.3",
        "click>=8.0",
        "colorama>=0.4",
        "commonmark>=0.9",
        "mergedeep>=1.3",
        "pycurl>=0.11",
        "rich>=10.3",
        "ruamel.yaml.clib>=0.2",
        "ruamel.yaml>=0.17",
        "toolz>=0.11",
    ],
)
