import sys
import platform

from setuptools import find_packages, setup

if sys.version_info < (3, 6):
    raise ValueError("This package requires python >= 3.6")

if platform.system() not in ['Windows', 'Darwin']:
    raise ValueError("This package only support Windows/MacOS.")

with open("requirements.txt") as fid:
    install_requires = [line.strip() for line in fid.readlines() if line]

with open("knowledge_exporter/__version__.py") as fid:
    for line in fid:
        if line.startswith("__version__"):
            version = line.strip().split()[-1][1:-1]
            break

with open("README.md") as fid:
    long_description = fid.read()

setup(
    name="knowledge-exporter",
    packages=find_packages(),
    package_data={"knowledge_exporter": ["bin/cpdf", "bin/cpdf.exe"]},
    scripts=["knowledge_exporter/bin/cpdf-wrapper"],
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Operating System :: MacOS",
        "Operating System :: Microsoft :: Windows",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    version=version,
    install_requires=install_requires,
    description="Export content from knowledge plaform.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Kada Liao",
    author_email="kadaliao@gmail.com",
    url="https://github.com/kadaliao/knowledge-exporter",
    keywords=["pdf", "knowledge", "download"],
    python_requires=">=3.6",
    entry_points={"console_scripts": ["knowledge-exporter=knowledge_exporter:main"]},
)
