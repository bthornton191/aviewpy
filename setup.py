import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="aviewpy",
    version="0.1.0",
    author="Ben Thornton",
    author_email="ben.thornton@mscsoftware.com",
    description="Python tools for working with Adams data",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/bthornton191/Adams_Modules",
    packages=setuptools.find_packages(exclude=['test']),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Microsoft :: Windows",
    ],
)