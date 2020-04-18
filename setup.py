from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="aws-embedded-metrics",
    version="1.0.2",
    author="Amazon Web Services",
    author_email="jarnance@amazon.com",
    description="AWS Embedded Metrics Package",
    long_description=long_description,
    long_description_content_type="text/markdown",
    keywords="aws logs metrics emf",
    url="https://github.com/awslabs/aws-embedded-metrics-python",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "License :: OSI Approved :: Apache Software License",
    ],
    packages=find_packages(exclude=["tests*"]),
    include_package_data=True,
    install_requires=["aiohttp"],
    test_suite="tests"
)
