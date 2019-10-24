from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="aws-embedded-metrics",
    version="0.0.1",
    author="Amazon Web Services",
    author_email="jaredcnance@gmail.com",

    description="AWS Embedded Metrics Package",
    long_description=long_description,
    long_description_content_type="text/markdown",

    keywords='aws xray sdk',

    url="https://github.com/awslabs/aws-embedded-metrics-python",

    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: Apache Software License',
    ],

    packages=find_packages(exclude=['tests*']),
    include_package_data=True
)
