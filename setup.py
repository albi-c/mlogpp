import setuptools

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

with open("mlogpp/__init__.py", encoding="utf-8") as f:
    exec(f.read())

setuptools.setup(
    name="mlogpp",
    version=__version__,
    author="albi-c",
    description="mlog++ to mindustry logic compiler",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/albi-c/mlog++",
    project_urls={
        "Bug Tracker": "https://github.com/albi-c/mlog++/issues"
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent"
    ],
    package_dir={"": "."},
    packages=setuptools.find_packages(),
    python_requires=">=3.6"
)
