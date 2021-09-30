from setuptools import setup

setup(
    name="shebanq",
    packages=[
        "modules",
    ],
    install_requires=[
        "markdown",
    ],
    python_requires=">=3.6.3",
    include_package_data=False,
    zip_safe=False,
    version='3.0.0',
    description="""Website for the BHSA (Hebrew Bible and ETCBC linguistics)""",
    author="Dirk Roorda",
    author_email="dirk.roorda@dans.knaw.nl",
    url="https://shebanq.ancient-data.org",
    keywords=[
        "text",
        "linguistics",
        "database",
        "hebrew",
        "bible",
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Other Environment",
        "Framework :: Web2Py",
        "Intended Audience :: Developers",
        "Intended Audience :: Education",
        "Intended Audience :: Religion",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Natural Language :: Hebrew",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows :: Windows 10",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: JavaScript",
        "Topic :: Religion",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Topic :: Sociology :: History",
        "Topic :: Text Processing :: Filters",
        "Topic :: Text Processing :: Linguistic",
        "Topic :: Text Processing :: Markup",
    ],
    long_description="""\
Website SHEBANQ.
""",
)
